import requests
import uuid


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def post(self, endpoint: str, payload=None, headers=None):
        url = f"{self.base_url}{endpoint}"

        final_headers = headers.copy() if headers else {}

        # Always ensure Idempotency-Key is present
        if "Idempotency-Key" not in final_headers:
            final_headers["Idempotency-Key"] = str(uuid.uuid4())

        return requests.post(
            url,
            json=payload,
            headers=final_headers
        )

    def get(self, endpoint: str, headers=None):
        url = f"{self.base_url}{endpoint}"
        return requests.get(url, headers=headers)
