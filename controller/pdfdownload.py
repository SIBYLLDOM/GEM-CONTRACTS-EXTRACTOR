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
        self.page.fill("#bno", "")
        self.page.fill("#bno", bid_no)

        # wait captcha
        self.page.wait_for_selector("#captchaimg1", timeout=15000)

        src = self.page.locator("#captchaimg1").get_attribute("src")
        img = Image.open(io.BytesIO(base64.b64decode(src.split(",")[1])))

        text, conf = ensemble_solve(img)
        if not text or conf < 0.55:
            raise Exception("Search CAPTCHA failed")

        self.page.fill("#captcha_code1", text)

        # IMPORTANT: click search AFTER captcha
        self.page.click("#searchlocation1")
        self.page.wait_for_timeout(4000)

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
            raise Exception("Popup CAPTCHA failed")

        self.page.fill("#captcha_code", text)
        self.page.click("#modelsbt")
        self.page.wait_for_timeout(3000)

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
        print("\n🚀 PHASE-2 START\n")

        pending = self.fetch_pending_bids()
        print(f"[PHASE-2] Total rows → {len(pending)}")

        for row in pending:
            bid_no = row["bid_no"]
            db_id = row["id"]

            print(f"[PHASE-2] Processing → {bid_no}")

            try:
                self.go_to_contracts()
                self.search_bid(bid_no)

                pdf_path = self.download_pdf(bid_no)

                cur = self.db.cursor()
                cur.execute(
                    "UPDATE contracts SET download_link=%s WHERE id=%s",
                    (pdf_path, db_id)
                )
                self.db.commit()
                cur.close()

                # update rowwise.txt
                self.rowwise_file.write_text(bid_no)

                print(f"[PDF] ✅ Saved → {pdf_path}")

                self.page.click("button[data-dismiss='modal']")
                self.page.wait_for_timeout(2000)

            except Exception as e:
                print(f"[PHASE-2] ❌ Failed → {bid_no} | {e}")
