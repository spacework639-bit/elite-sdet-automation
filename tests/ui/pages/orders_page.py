import os

# Environment-driven base URL
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class OrdersPage:
    def __init__(self, page):
        self.page = page

    # ---------------------------------------------------------
    # OPEN CANCEL ORDER PAGE (FRONTEND)
    # ---------------------------------------------------------
    def open_cancel_order_api(self):
        self.page.goto(f"{BASE_URL}/frontend/cancel_order.html")

        # wait until the UI element actually appears
        order_input = self.page.locator("#order_id")

        order_input.wait_for(state="visible")

    # ---------------------------------------------------------
    # CANCEL ORDER VIA FRONTEND
    # ---------------------------------------------------------
    def cancel_order_via_swagger(self, order_id: int):

        self.page.fill("#order_id", str(order_id))

        with self.page.expect_response(
            lambda response: (
                f"/orders/{order_id}/cancel" in response.url
                and response.request.method == "POST"
            )
        ) as response_info:

            self.page.click("#cancel_btn")

        return response_info.value