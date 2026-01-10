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
    # CATEGORY CSV
    # --------------------------------------------------
    def _load_categories(self):
        with open(self.category_csv, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

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
    # CATEGORY SEARCH
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
            if options.nth(i).inner_text().strip().lower() == category.lower():
                options.nth(i).click()
                return

        raise Exception(f"Category exact match missing → {category}")

    # --------------------------------------------------
    # MAIN CAPTCHA
    # --------------------------------------------------
    def solve_main_captcha_and_search(self):
        src = self.page.locator("#captchaimg1").get_attribute("src")
        img = Image.open(io.BytesIO(base64.b64decode(src.split(",")[1])))
        text, conf = ensemble_solve(img)

        if not text or conf < 0.55:
            raise Exception("Main CAPTCHA failed")

        self.page.fill("#captcha_code1", text)
        self.page.click("#searchlocation1")
        self.page.wait_for_timeout(4000)

    # --------------------------------------------------
    # PHASE-1 — ROW SCRAPING ONLY
    # --------------------------------------------------
    def phase1_scrape_rows(self, category):
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
    # MAIN LOOP (PHASE-1 ONLY)
    # --------------------------------------------------
    def run(self):
        print("🚀 PHASE-1 START")
        for idx, row in enumerate(self.categories, start=1):
            category = row["category_name"]

            print(f"\n[{idx}/{len(self.categories)}] Processing → {category}")

            self.reset_to_home()
            self.go_to_gem_contracts()
            self.process_category(category)
            self.set_date_filter()
            self.solve_main_captcha_and_search()
            self.phase1_scrape_rows(category)

        print("🎉 PHASE-1 COMPLETED SUCCESSFULLY")
