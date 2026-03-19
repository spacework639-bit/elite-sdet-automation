from playwright.sync_api import expect
import os

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class ProductsPage:
    def __init__(self, page):
        self.page = page

    # ---------------------------------------------------------
    # OPEN CREATE ORDER PAGE (FRONTEND)
    # ---------------------------------------------------------
    def open_orders_api(self):
        self.page.goto(
            f"{BASE_URL}/frontend/place_order.html",
            wait_until="domcontentloaded"
        )

        expect(self.page.locator("#product_id")).to_be_visible()

    # ---------------------------------------------------------
    # PLACE ORDER VIA FRONTEND
    # ---------------------------------------------------------
    def place_order_via_swagger(self, product_id: int, quantity: int, idempotency_key: str):
        self.page.fill("#product_id", str(product_id))
        self.page.fill("#quantity", str(quantity))

        with self.page.expect_response(
            lambda r: "/orders" in r.url and r.request.method == "POST"
        ) as response_info:

            self.page.locator("#place_order_btn").click()

        return response_info.value