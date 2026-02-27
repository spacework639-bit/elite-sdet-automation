from playwright.sync_api import expect
import os

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
class ProductsPage:
    def __init__(self, page):
        self.page = page

    # ---------------------------------------------------------
    # OPEN CREATE ORDER ENDPOINT
    # ---------------------------------------------------------
       # ---------------------------------------------------------
    # OPEN CREATE ORDER ENDPOINT
    # ---------------------------------------------------------
    def open_orders_api(self):
        self.page.goto(
            f"{BASE_URL}/docs#/default/create_order_orders_post",
            wait_until="domcontentloaded"
        )

        expect(
            self.page.locator(
                "#operations-default-create_order_orders_post"
            )
        ).to_be_visible()

    # ---------------------------------------------------------
    # INTERNAL: GET CREATE ORDER BLOCK
    # ---------------------------------------------------------
    def _get_create_order_block(self):
        return self.page.locator(
            "#operations-default-create_order_orders_post"
        )

    # ---------------------------------------------------------
    # PLACE ORDER VIA SWAGGER (NETWORK-DRIVEN)
    # ---------------------------------------------------------
    def place_order_via_swagger(
        self,
        product_id: int,
        quantity: int,
        idempotency_key: str
    ):
        endpoint = self._get_create_order_block()

        # Expand if collapsed
        classes = endpoint.get_attribute("class") or ""
        if "is-open" not in classes:
            endpoint.locator(".opblock-summary").click()

        # Click "Try it out" only if visible
        try_button = endpoint.locator("button:has-text('Try it out')")
        if try_button.count() > 0 and try_button.is_visible():
            try_button.click()

        # Wait for request textarea
        request_body = endpoint.locator("textarea").first
        expect(request_body).to_be_visible()

        # Fill request body
        request_body.fill(
            f'{{"product_id": {product_id}, "quantity": {quantity}}}'
        )

        # Fill Idempotency-Key header
        endpoint.locator(
            'input[placeholder="Idempotency-Key"]'
        ).fill(idempotency_key)

        # Wait for real network response
        with self.page.expect_response(
            lambda response: (
                "/orders" in response.url
                and response.request.method == "POST"
            )
        ) as response_info:

            endpoint.locator("button:has-text('Execute')").click()

        return response_info.value.text()
