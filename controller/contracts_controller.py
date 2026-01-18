import csv
import base64
import io
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image

import mysql.connector
from mysql.connector import Error

from solver.captcha_solver import ensemble_solve


# --------------------------------------------------
# DATABASE CONFIG
# --------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "tender_automation_with_ai"
}


class ContractsController:
    def __init__(self, browser):
        self.browser = browser
        self.page = browser.page

        base = Path(__file__).resolve().parents[1]
        self.category_csv = base / "data" / "Datasets" / "categories.csv"

        self.categories = self._load_categories()

        self.retry_counts = {}
        self.max_retries = 6

        self.db = self._connect_db()
        self._create_table()

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

    def _create_table(self):
        cur = self.db.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            serial_no INT,
            category_name VARCHAR(255),
            bid_no VARCHAR(100),
            product TEXT,
            brand VARCHAR(255),
            model VARCHAR(255),
            ordered_quantity VARCHAR(50),
            price VARCHAR(50),
            total_value VARCHAR(50),
            buyer_dept_org TEXT,
            organization_name TEXT,
            buyer_designation TEXT,
            state VARCHAR(100),
            buyer_department TEXT,
            office_zone TEXT,
            buying_mode VARCHAR(100),
            contract_date VARCHAR(100),
            order_status VARCHAR(100),
            download_link TEXT
        )
        """)
        self.db.commit()
        cur.close()

    # --------------------------------------------------
    # CATEGORY CSV (CLEAN + SAFE APPEND)
    # --------------------------------------------------
    def _load_categories(self):
        if not self.category_csv.exists():
            return []

        clean_rows = []
        with open(self.category_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("category_name", "").strip():
                    clean_rows.append({
                        "si_no": int(row["si_no"]),
                        "category_name": row["category_name"].strip()
                    })
        return clean_rows

    def _append_category(self, name, force=False):
        name = name.strip()
        if not name:
            return

        # Check if it's already in our memory list to avoid CSV duplication
        # We use a case-insensitive check to identify duplicates
        existing_names = {c["category_name"].lower() for c in self.categories}
        
        is_duplicate = name.lower() in existing_names

        # If it's a new discovery (not in memory), append to CSV
        if not is_duplicate:
            next_si = len(self.categories) + 1
            file_exists = self.category_csv.exists()
            with open(self.category_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["si_no", "category_name"])
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    "si_no": next_si,
                    "category_name": name
                })
            
            self.categories.append({
                "si_no": next_si,
                "category_name": name
            })
            print(f"[CSV] ➕ Appended new category → {name}")

        elif force:
            # If it's a retry (force=True), we add it to the memory list for processing
            # but we DON'T write to CSV because it's already there
            next_si = len(self.categories) + 1
            self.categories.append({
                "si_no": next_si,
                "category_name": name
            })
            print(f"[RETRY] 🔄 Category re-queued for processing → {name}")

    # --------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------
    def reset_to_home(self):
        self.page.goto("https://gem.gov.in/", timeout=60000)
        self.page.wait_for_timeout(3000)

    def go_to_gem_contracts(self):
        self.page.wait_for_selector("ul#nav", timeout=60000)
        self.page.click('ul#nav a[title="View Contracts "]')
        self.page.wait_for_timeout(1000)
        self.page.click('ul#nav a[href="https://gem.gov.in/view_contracts"]')
        self.page.wait_for_timeout(3000)

    # --------------------------------------------------
    # DATE FILTER
    # --------------------------------------------------
    def set_date_filter(self):
        to_date = datetime.today()
        from_date = to_date - timedelta(days=2)

        self.page.evaluate("""
        (d)=>{
            document.querySelector('#from_date_contract_search1').value=d.from;
            document.querySelector('#to_date_contract_search1').value=d.to;
        }
        """, {
            "from": from_date.strftime("%d-%m-%Y"),
            "to": to_date.strftime("%d-%m-%Y")
        })

    # --------------------------------------------------
    # CATEGORY SEARCH + CSV AUTO APPEND
    # --------------------------------------------------
    def process_category(self, category):
        self.page.click(".select2-selection")
        self.page.wait_for_selector("input.select2-search__field")

        search = self.page.locator("input.select2-search__field")
        search.fill(category)
        self.page.wait_for_timeout(1500)

        options = self.page.locator(
            "li.select2-results__option:not(.select2-results__message)"
        )

        for i in range(options.count()):
            txt = options.nth(i).inner_text().strip()
            self._append_category(txt)

        for i in range(options.count()):
            if options.nth(i).inner_text().strip().lower() == category.lower():
                options.nth(i).click()
                return

        raise Exception(f"Category exact match missing → {category}")

    # --------------------------------------------------
    # CAPTCHA
    # --------------------------------------------------
    def solve_main_captcha_and_search(self):
        """Solves CAPTCHA and returns True if search initiated, False if CAPTCHA error"""
        src = self.page.locator("#captchaimg1").get_attribute("src")
        img = Image.open(io.BytesIO(base64.b64decode(src.split(",")[1])))

        text, conf = ensemble_solve(img)
        if not text or conf < 0.55:
            print("[CAPTCHA] ❌ Low confidence or OCR failed")
            return False

        self.page.fill("#captcha_code1", text)
        self.page.click("#searchlocation1")
        
        # Wait for the page to either show results, no result, or an error
        self.page.wait_for_timeout(4000)

        # Check for error message using specific locator mentioned by user
        # We check both visibility and content to be absolutely sure
        pcaptcha_error = self.page.locator("#pcaptcha_code1")
        
        if pcaptcha_error.is_visible():
            err_text = pcaptcha_error.inner_text().strip()
            if "Please enter correct Confirmation Code" in err_text or "Enter captcha code" in err_text:
                print(f"[CAPTCHA] ❌ Error: {err_text}")
                return False
        
        return True

    # --------------------------------------------------
    # NO RESULT CHECK
    # --------------------------------------------------
    def has_no_result(self):
        loc = self.page.locator("div[style*='color:red']")
        return loc.count() > 0 and "No Result Found" in loc.first.inner_text()

    # --------------------------------------------------
    # PHASE-1 ROW SCRAPING (UNCHANGED LOGIC)
    # --------------------------------------------------
    def phase1_scrape_rows(self, category):
        if self.has_no_result():
            print(f"[SKIP] No Result Found → {category}")
            return

        self.page.wait_for_selector("span.ajxtag_order_number", timeout=30000)

        bids = self.page.locator("span.ajxtag_order_number")
        items = self.page.locator("span.ajxtag_item_title")
        qtys = self.page.locator("span.ajxtag_quantity")
        values = self.page.locator("span.ajxtag_totalvalue")
        buyers = self.page.locator("span.ajxtag_buyer_dept_org")
        modes = self.page.locator("span.ajxtag_buying_mode")
        dates = self.page.locator("span.ajxtag_contract_date")
        status = self.page.locator("span.ajxtag_order_status")

        cur = self.db.cursor()

        for i in range(bids.count()):
            row = (
                i + 1, category, bids.nth(i).inner_text().strip(),
                items.nth(i*3).inner_text().strip(),
                items.nth(i*3+1).inner_text().strip(),
                items.nth(i*3+2).inner_text().strip(),
                qtys.nth(i).inner_text().strip(),
                values.nth(i*2+1).inner_text().strip(),
                values.nth(i*2).inner_text().strip(),
                buyers.nth(i*3).inner_text().strip(),
                buyers.nth(i*3+1).inner_text().strip(),
                buyers.nth(i*3+2).inner_text().strip(),
                modes.nth(i*4).inner_text().strip(),
                modes.nth(i*4+1).inner_text().strip(),
                modes.nth(i*4+2).inner_text().strip(),
                modes.nth(i*4+3).inner_text().strip(),
                dates.nth(i).inner_text().strip(),
                status.nth(i).inner_text().strip(),
                None
            )

            cur.execute("""
            INSERT INTO contracts (
                serial_no, category_name, bid_no,
                product, brand, model,
                ordered_quantity, price, total_value,
                buyer_dept_org, organization_name, buyer_designation,
                state, buyer_department, office_zone, buying_mode,
                contract_date, order_status, download_link
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, row)

        self.db.commit()
        cur.close()
        print(f"[PHASE-1] Completed → {category}")

    # --------------------------------------------------
    # MAIN LOOP (PHASE-1)
    # --------------------------------------------------
    def run(self):
        print("🚀 PHASE-1 START")
        
        # Use simple index to allow self.categories to grow dynamically
        i = 0
        while i < len(self.categories):
            row = self.categories[i]
            category = row["category_name"]
            print(f"\n[{i+1}/{len(self.categories)}] Processing → {category}")

            try:
                self.reset_to_home()
                self.go_to_gem_contracts()
                self.process_category(category)
                self.set_date_filter()
                
                if not self.solve_main_captcha_and_search():
                    # Increment retry count
                    count = self.retry_counts.get(category, 0) + 1
                    self.retry_counts[category] = count
                    
                    if count < self.max_retries:
                        print(f"[FAIL] CAPTCHA failed for {category} (Attempt {count}/{self.max_retries}). Queuing for retry...")
                        self._append_category(category, force=True)
                    else:
                        print(f"[LIMIT] 🛑 Max retries ({self.max_retries}) reached for {category}. Moving on.")
                else:
                    self.phase1_scrape_rows(category)
                    
            except Exception as e:
                print(f"[ERROR] Failed category {category}: {e}")
                
                # Increment retry count for exceptions too
                count = self.retry_counts.get(category, 0) + 1
                self.retry_counts[category] = count
                
                if count < self.max_retries:
                    print(f"Queuing {category} for retry (Attempt {count}/{self.max_retries})...")
                    self._append_category(category, force=True)
                else:
                    print(f"[LIMIT] 🛑 Max retries ({self.max_retries}) reached for {category}. Moving on.")

            i += 1

        print("🎉 PHASE-1 COMPLETED SUCCESSFULLY")
