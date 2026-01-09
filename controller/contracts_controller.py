import csv
import base64
import io
from datetime import datetime, timedelta
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


class ContractsController:
    def __init__(self, browser):
        self.browser = browser
        self.page = browser.page

        base_path = Path(__file__).resolve().parents[1]

        self.category_csv = base_path / "data" / "Datasets" / "categories.csv"
        self.output_dir = base_path / "data" / "scrapped"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.output_csv = self.output_dir / "contracts_merged.csv"
        self._init_output_csv()

        with open(self.category_csv, newline="", encoding="utf-8") as f:
            self.categories = list(csv.DictReader(f))

        # DB INIT
        self.db = self._connect_db()
        self._create_table()

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------
    def _connect_db(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            print("[DB] ✅ Connected to database")
            return conn
        except Error as e:
            print(f"[DB] ❌ Connection failed: {e}")
            return None

    def _create_table(self):
        if not self.db:
            return

        query = """
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
            download_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cur = self.db.cursor()
        cur.execute(query)
        self.db.commit()
        cur.close()
        print("[DB] ✅ Table ready")

    def save_row(self, row):
        # CSV
        with open(self.output_csv, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

        # DB
        if not self.db:
            return

        query = """
        INSERT INTO contracts (
            serial_no, category_name, bid_no, product, brand, model,
            ordered_quantity, price, total_value,
            buyer_dept_org, organization_name, buyer_designation,
            state, buyer_department, office_zone, buying_mode,
            contract_date, order_status, download_link
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cur = self.db.cursor()
        cur.execute(query, row)
        self.db.commit()
        cur.close()

    # --------------------------------------------------
    # CSV INIT
    # --------------------------------------------------
    def _init_output_csv(self):
        if not self.output_csv.exists():
            with open(self.output_csv, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    "serial_no", "category_name", "bid_no",
                    "product", "brand", "model",
                    "ordered_quantity", "price", "total_value",
                    "buyer_dept_org", "organization_name", "buyer_designation",
                    "state", "buyer_department", "office_zone", "buying_mode",
                    "contract_date", "order_status", "download_link"
                ])

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

        self.page.evaluate(
            """
            (d) => {
                document.querySelector('#from_date_contract_search1').value = d.from;
                document.querySelector('#to_date_contract_search1').value = d.to;
                document.querySelector('#from_date_contract_search1').dispatchEvent(new Event('change'));
                document.querySelector('#to_date_contract_search1').dispatchEvent(new Event('change'));
            }
            """,
            {
                "from": from_date.strftime("%d-%m-%Y"),
                "to": to_date.strftime("%d-%m-%Y")
            }
        )

    # --------------------------------------------------
    # CATEGORY
    # --------------------------------------------------
    def process_category(self, category_name):
        self.page.click(".select2-selection")
        self.page.wait_for_selector("input.select2-search__field")

        search = self.page.locator("input.select2-search__field")
        search.clear()
        search.fill(category_name)
        self.page.wait_for_timeout(1500)

        options = self.page.locator(
            "li.select2-results__option:not(.select2-results__message)"
        )

        for i in range(options.count()):
            if options.nth(i).inner_text().strip().lower() == category_name.lower():
                options.nth(i).click()
                self.page.wait_for_timeout(1000)
                return

        raise Exception("Category not found")

    # --------------------------------------------------
    # CAPTCHA
    # --------------------------------------------------
    def solve_main_captcha_and_search(self):
        src = self.page.locator("#captchaimg1").get_attribute("src")
        img = Image.open(io.BytesIO(base64.b64decode(src.split(",")[1])))

        text, conf = ensemble_solve(img)
        if not text or conf < 0.55:
            raise Exception("Main captcha failed")

        self.page.fill("#captcha_code1", text)
        self.page.click("#searchlocation1")
        self.page.wait_for_timeout(4000)

    # --------------------------------------------------
    # NO RESULT
    # --------------------------------------------------
    def has_no_result(self):
        loc = self.page.locator('div[style*="color:red"]')
        return loc.count() > 0 and "No Result Found" in loc.first.inner_text()

    # --------------------------------------------------
    # ROWS
    # --------------------------------------------------
    def process_rows(self, category_name):
        if self.has_no_result():
            print(f"[SKIP] No Result Found → {category_name}")
            return

        self.page.wait_for_selector("span.ajxtag_order_number", timeout=30000)

        bid_nodes = self.page.locator("span.ajxtag_order_number")
        item_nodes = self.page.locator("span.ajxtag_item_title")
        qty_nodes = self.page.locator("span.ajxtag_quantity")
        value_nodes = self.page.locator("span.ajxtag_totalvalue")
        buyer_nodes = self.page.locator("span.ajxtag_buyer_dept_org")
        mode_nodes = self.page.locator("span.ajxtag_buying_mode")
        date_nodes = self.page.locator("span.ajxtag_contract_date")
        status_nodes = self.page.locator("span.ajxtag_order_status")

        total = bid_nodes.count()
        print(f"[INFO] Total tenders: {total}")

        for i in range(total):
            row = [
                i + 1,
                category_name,
                bid_nodes.nth(i).inner_text().strip(),
                item_nodes.nth(i*3).inner_text().strip(),
                item_nodes.nth(i*3+1).inner_text().strip(),
                item_nodes.nth(i*3+2).inner_text().strip(),
                qty_nodes.nth(i).inner_text().strip(),
                value_nodes.nth(i*2+1).inner_text().strip(),
                value_nodes.nth(i*2).inner_text().strip(),
                buyer_nodes.nth(i*3).inner_text().strip(),
                buyer_nodes.nth(i*3+1).inner_text().strip(),
                buyer_nodes.nth(i*3+2).inner_text().strip(),
                mode_nodes.nth(i*4).inner_text().strip(),
                mode_nodes.nth(i*4+1).inner_text().strip(),
                mode_nodes.nth(i*4+2).inner_text().strip(),
                mode_nodes.nth(i*4+3).inner_text().strip(),
                date_nodes.nth(i).inner_text().strip(),
                status_nodes.nth(i).inner_text().strip(),
                ""
            ]

            bid_nodes.nth(i).click()
            self.page.wait_for_timeout(2000)

            src = self.page.locator("#captchaimg").get_attribute("src")
            img = Image.open(io.BytesIO(base64.b64decode(src.split(",")[1])))
            text, conf = ensemble_solve(img)

            if text and conf >= 0.55:
                self.page.fill("#captcha_code", text)
                self.page.click("#modelsbt")
                self.page.wait_for_timeout(3000)
                row[-1] = self.page.locator("a#dwnbtn").get_attribute("href")

            self.save_row(row)
            print(f"[ROW] Saved {row[2]}")

            self.page.click("button[data-dismiss='modal']")
            self.page.wait_for_timeout(2000)

    # --------------------------------------------------
    # MAIN RUN METHOD  ✅ eeeTHIS FIXES YOUR ERROR
    # --------------------------------------------------
    def run(self):
        for idx, row in enumerate(self.categories, start=1):
            category = row["category_name"]

            print("\n" + "=" * 70)
            print(f"🚀 CATEGORY {idx}/{len(self.categories)} → {category}")
            print("=" * 70)

            self.reset_to_home()
            self.go_to_gem_contracts()
            self.process_category(category)
            self.set_date_filter()
            self.solve_main_captcha_and_search()
            self.process_rows(category)
