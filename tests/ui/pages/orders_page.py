from playwright.sync_api import expect


class OrdersPage:
    def __init__(self, page):
        self.page = page

    # ---------------------------------------------------------
    # OPEN CANCEL ORDER ENDPOINT
    # ---------------------------------------------------------
    def open_cancel_order_api(self):
        self.page.goto(
            "http://127.0.0.1:8000/docs#/default/cancel_order_orders__order_id__cancel_post",
            wait_until="domcontentloaded"
        )

        expect(
            self.page.locator(
                "#operations-default-cancel_order_orders__order_id__cancel_post"
            )
        ).to_be_visible()

    # ---------------------------------------------------------
    # INTERNAL: GET CANCEL BLOCK
    # ---------------------------------------------------------
    def _get_cancel_block(self):
        return self.page.locator(
            "#operations-default-cancel_order_orders__order_id__cancel_post"
        )

    # ---------------------------------------------------------
    # CANCEL ORDER VIA SWAGGER (SCOPED + NETWORK-DRIVEN)
    # ---------------------------------------------------------
    def cancel_order_via_swagger(self, order_id: int):
        endpoint = self._get_cancel_block()

        # Expand if collapsed
        classes = endpoint.get_attribute("class") or ""
        if "is-open" not in classes:
            endpoint.locator(".opblock-summary").click()

        # Click "Try it out" only if visible
        try_button = endpoint.locator("button:has-text('Try it out')")
        if try_button.count() > 0 and try_button.is_visible():
            try_button.click()

        # Locate parameter row safely
        param_row = endpoint.locator("tr[data-param-name='order_id']")

        expect(param_row).to_be_visible()

        order_input = param_row.locator("input")
        expect(order_input).to_be_visible()

        order_input.fill(str(order_id))

        # Wait for network response
        with self.page.expect_response(
            lambda response: (
                f"/orders/{order_id}/cancel" in response.url
                and response.request.method == "POST"
            )
        ) as response_info:

            endpoint.locator("button:has-text('Execute')").click()

        return response_info.value
