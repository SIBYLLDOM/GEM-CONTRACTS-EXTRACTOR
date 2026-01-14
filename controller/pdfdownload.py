import base64
import io
from pathlib import Path
from PIL import Image

import mysql.connector
from mysql.connector import Error

from solver.captcha_solver import ensemble_solve


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "tender_automation_with_ai"
}


class PDFDownloader:
    def __init__(self, browser):
        self.browser = browser
        self.page = browser.page

        base = Path(__file__).resolve().parents[1]

        self.pdf_dir = base / "data" / "ContractPDF"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

        self.rowwise_file = base / "data" / "rowwise.txt"

        self.db = self._connect_db()

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------
    def _connect_db(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            print("[DB] ✅ Connected")
            return conn
        except Error as e:
            raise RuntimeError(e)

    # --------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------
    def go_to_contracts(self):
        self.page.goto("https://gem.gov.in/view_contracts", timeout=60000)
        self.page.wait_for_timeout(3000)

    # --------------------------------------------------
    # FETCH PENDING BIDS
    # --------------------------------------------------
    def fetch_pending_bids(self):
        cur = self.db.cursor(dictionary=True)
        cur.execute("""
            SELECT id, bid_no
            FROM contracts
            WHERE download_link IS NULL
            ORDER BY id ASC
        """)
        rows = cur.fetchall()
        cur.close()
        return rows

    # --------------------------------------------------
    # SEARCH BID + CAPTCHA + SEARCH CLICK
    # --------------------------------------------------
    def search_bid(self, bid_no):
        """Returns True if search success, False if captcha error"""
        self.page.fill("#bno", "")
        self.page.fill("#bno", bid_no)

        # wait captcha
        self.page.wait_for_selector("#captchaimg1", timeout=15000)

        src = self.page.locator("#captchaimg1").get_attribute("src")
        img = Image.open(io.BytesIO(base64.b64decode(src.split(",")[1])))

        text, conf = ensemble_solve(img)
        if not text or conf < 0.55:
            print("[CAPTCHA] ❌ Low confidence on Search CAPTCHA")
            return False

        self.page.fill("#captcha_code1", text)
        self.page.click("#searchlocation1")
        self.page.wait_for_timeout(4000)

        # Check for red error message
        pcaptcha_error = self.page.locator("#pcaptcha_code1")
        if pcaptcha_error.is_visible():
            err_text = pcaptcha_error.inner_text().strip()
            if "Please enter correct Confirmation Code" in err_text:
                print(f"[CAPTCHA] ❌ Search Error: {err_text}")
                return False
        
        return True

    # --------------------------------------------------
    # DOWNLOAD PDF
    # --------------------------------------------------
    def download_pdf(self, bid_no):
        self.page.wait_for_selector("span.ajxtag_order_number", timeout=15000)

        card = self.page.locator(
            f"span.ajxtag_order_number:text('{bid_no}')"
        )

        if card.count() == 0:
            raise Exception("Tender card not found")

        card.first.click()
        self.page.wait_for_timeout(2000)

        # popup captcha
        src = self.page.locator("#captchaimg").get_attribute("src")
        img = Image.open(io.BytesIO(base64.b64decode(src.split(",")[1])))
        text, conf = ensemble_solve(img)

        if not text or conf < 0.55:
            print("[CAPTCHA] ❌ Low confidence on Popup CAPTCHA")
            return "RETRY"

        self.page.fill("#captcha_code", text)
        self.page.click("#modelsbt")
        self.page.wait_for_timeout(3000)

        # Check for red error message in popup
        # Specifically checking the ID mentioned by user
        pcaptcha_error = self.page.locator("#pcaptcha_code1")
        if pcaptcha_error.is_visible():
            err_text = pcaptcha_error.inner_text().strip()
            if "Please enter correct Confirmation Code" in err_text:
                print(f"[CAPTCHA] ❌ Popup Error: {err_text}")
                return "RETRY"
        
        # Fallback for alternative ID just in case
        pcaptcha_alt = self.page.locator("#pcaptcha_code")
        if pcaptcha_alt.is_visible():
            if "Please enter" in pcaptcha_alt.inner_text():
                return "RETRY"

        with self.page.expect_download(timeout=20000) as d:
            self.page.locator("a#dwnbtn").click()

        pdf = d.value
        pdf_path = self.pdf_dir / f"{bid_no}.pdf"
        pdf.save_as(pdf_path)

        return str(pdf_path)

    # --------------------------------------------------
    # MAIN PHASE-2 LOGIC
    # --------------------------------------------------
    def run(self):
        print("\n🚀 PHASE-2 START (Persistent Mode)\n")

        while True:
            # Re-fetch only rows that are STILL null
            pending = self.fetch_pending_bids()
            
            if not pending:
                print("\n" + "="*50)
                print("🎉 ALL DOWNLOADS COMPLETE! No NULL links left.")
                print("="*50)
                break

            print(f"\n[PHASE-2] {len(pending)} rows remaining with NULL links. Starting processing pass...")

            i = 0
            # Use local list for the current pass
            current_queue = pending.copy()
            while i < len(current_queue):
                row = current_queue[i]
                bid_no = row["bid_no"]
                db_id = row["id"]

                print(f"\n[{i+1}/{len(current_queue)}] Working on → {bid_no}")

                try:
                    self.go_to_contracts()
                    
                    # Step 1: Search Bid
                    if not self.search_bid(bid_no):
                        print(f"[RETRY] 🔄 CAPTCHA failed on Search. Moving {bid_no} to end of queue.")
                        current_queue.append(row)
                    else:
                        # Step 2: Download PDF
                        download_status = self.download_pdf(bid_no)
                        
                        if download_status == "RETRY":
                            print(f"[RETRY] 🔄 CAPTCHA failed on Popup. Moving {bid_no} to end of queue.")
                            current_queue.append(row)
                            try: self.page.click("button[data-dismiss='modal']", timeout=2000)
                            except: pass
                        else:
                            pdf_path = download_status
                            # UPDATE DATABASE
                            cur = self.db.cursor()
                            cur.execute(
                                "UPDATE contracts SET download_link=%s WHERE id=%s",
                                (pdf_path, db_id)
                            )
                            self.db.commit()
                            cur.close()

                            print(f"[PDF] ✅ SUCCESS! Link updated in DB → {bid_no}")
                            
                            try: self.page.click("button[data-dismiss='modal']", timeout=2000)
                            except: pass

                except Exception as e:
                    print(f"[ERROR] ❌ Exception for {bid_no}: {e}")
                    current_queue.append(row)
                
                i += 1
                # Small delay to prevent too many DB queries in a tight loop
                if i >= len(current_queue):
                    print("\n[PASS] Current pass finished. Scanning database for remaining NULLs...")
                    self.page.wait_for_timeout(2000)

        print("\n🎉 PHASE-2 COMPLETED SUCCESSFULLY")
