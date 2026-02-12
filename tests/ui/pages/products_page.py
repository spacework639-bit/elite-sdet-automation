import json
import time

class ProductsPage:
    def __init__(self, page):
        self.page = page

    def open_orders_api(self):
        # Open Swagger directly on POST /orders
        self.page.goto(
            "http://127.0.0.1:8000/docs#/default/create_order_orders_post",
            wait_until="domcontentloaded"
        )

        # Let Swagger fully render``
        self.page.wait_for_timeout(3000)

    def place_order_via_swagger(self, product_id, quantity, idempotency_key):
        """
        DEMO MODE:
        - Click Try it out
        - Fill payload
        - Fill Idempotency-Key
        - Click Execute
        """

        # Click "Try it out"
        self.page.locator("button:has-text('Try it out')").first.click()
        self.page.wait_for_timeout(1000)

        # Swagger renders multiple textareas.
        # The LAST one is the actual request body.
        request_body = self.page.locator("textarea").last

        # Clear default example
        request_body.click()
        request_body.fill("")

        payload = json.dumps(
            {
                "product_id": product_id,
                "quantity": quantity
            },
            indent=2
        )
        request_body.fill(payload)

        # Fill Idempotency-Key header input
        self.page.locator(
            'input[placeholder="Idempotency-Key"]'
        ).fill(idempotency_key)

        self.page.wait_for_timeout(1000)

        # Click Execute
        self.page.locator("button:has-text('Execute')").click()

        # Wait for response to render
        self.page.wait_for_timeout(3000)

        # Swagger renders multiple response blocks.
        # The LAST one is the executed response.
        response_block = self.page.locator("pre.microlight").last
        response_text = response_block.inner_text()

        return response_text
