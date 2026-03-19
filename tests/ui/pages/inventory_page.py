import os
from playwright.sync_api import expect

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class InventoryPage:

    def __init__(self, page):
        self.page = page

    # ---------------------------------------------------------
    # OPEN RESTOCK PAGE
    # ---------------------------------------------------------
    def open_restock_api(self):

        self.page.goto(f"{BASE_URL}/frontend/restock_inventory.html")

        expect(self.page.locator("#product_id")).to_be_visible()

    # ---------------------------------------------------------
    # RESTOCK INVENTORY VIA FRONTEND
    # ---------------------------------------------------------
    def restock_via_swagger(self, product_id: int, quantity: int):

        self.page.fill("#product_id", str(product_id))
        self.page.fill("#quantity", str(quantity))

        with self.page.expect_response(
            lambda r: "/inventory" in r.url and r.request.method == "POST"
        ) as response_info:

            self.page.click("#restock_btn")

        return response_info.value