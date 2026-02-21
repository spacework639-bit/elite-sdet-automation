from playwright.sync_api import expect


class InventoryPage:
    def __init__(self, page):
        self.page = page

    # ---------------------------------------------------------
    # OPEN RESTOCK ENDPOINT
    # ---------------------------------------------------------
    def open_restock_api(self):
        self.page.goto(
            "http://127.0.0.1:8000/docs#/default/restock_inventory_inventory_restock_post",
            wait_until="domcontentloaded"
        )

        expect(
            self.page.locator(
                "#operations-default-restock_inventory_inventory_restock_post"
            )
        ).to_be_visible()

    # ---------------------------------------------------------
    # INTERNAL: GET RESTOCK BLOCK
    # ---------------------------------------------------------
    def _get_restock_block(self):
        return self.page.locator(
            "#operations-default-restock_inventory_inventory_restock_post"
        )

    # ---------------------------------------------------------
    # RESTOCK VIA SWAGGER (NETWORK-DRIVEN)
    # ---------------------------------------------------------
    def restock_via_swagger(self, product_id: int, quantity: int):
        endpoint = self._get_restock_block()

        # Expand if collapsed
        classes = endpoint.get_attribute("class") or ""
        if "is-open" not in classes:
            endpoint.locator(".opblock-summary").click()

        # Click Try it out if visible
        try_button = endpoint.locator("button:has-text('Try it out')")
        if try_button.count() > 0 and try_button.is_visible():
            try_button.click()

        # Wait for textarea
        request_body = endpoint.locator("textarea").first
        expect(request_body).to_be_visible()

        request_body.fill(
            f'{{"product_id": {product_id}, "quantity": {quantity}}}'
        )

        # Network-driven execution
        with self.page.expect_response(
            lambda response: (
                "/inventory/restock" in response.url
                and response.request.method == "POST"
            )
        ) as response_info:

            endpoint.locator("button:has-text('Execute')").click()

        return response_info.value
