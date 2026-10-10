import asyncio

import httpx

from shipment_cutouts.background_client import BackgroundClient


def test_request_uses_exact_background_remove_boundary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/image/background_remove"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Idempotency-Key"] == "shipment-1"
        assert request.read() == b'{"image":{"base64":"aW1hZ2U="},"format":"png"}'
        return httpx.Response(
            200,
            json={
                "ok": True,
                "data": {"id": "processed-image"},
                "error": None,
                "metadata": {"vendor": "selected"},
            },
        )

    client = BackgroundClient(
        api_key="test-key", transport=httpx.MockTransport(handler)
    )

    result = asyncio.run(client.remove({"base64": "aW1hZ2U="}, "png", "shipment-1"))

    assert result == {"id": "processed-image"}
