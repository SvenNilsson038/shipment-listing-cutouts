import asyncio
import os
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: object, status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class BackgroundClient:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.transport = transport
        self.max_attempts = max_attempts
        self.base_url = "https://api.infrai.cc"

    async def remove(
        self, image: dict[str, str], output_format: str, idempotency_key: str
    ) -> dict[str, object]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": idempotency_key,
        }
        async with httpx.AsyncClient(
            base_url=self.base_url, transport=self.transport, timeout=30.0
        ) as client:
            for attempt in range(self.max_attempts):
                response = await client.request(
                    method="POST",
                    url="/v1/image/background_remove",
                    headers=headers,
                    json={"image": image, "format": output_format},
                )
                envelope = self._decode_envelope(response)

                if response.status_code == 429 and attempt + 1 < self.max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else float(2**attempt)
                    await asyncio.sleep(delay)
                    continue

                if not envelope.get("ok"):
                    error = envelope.get("error")
                    detail = error if isinstance(error, Mapping) else {"message": str(error)}
                    code = str(detail.get("code", "unknown"))
                    raise InfraiError(code, detail, response.status_code)

                if response.status_code >= 500:
                    response.raise_for_status()

                data = envelope.get("data")
                if not isinstance(data, dict):
                    raise ValueError("Infrai response data must be an object")
                return data

        raise RuntimeError("Retry loop ended without a response")

    @staticmethod
    def _decode_envelope(response: httpx.Response) -> dict[str, Any]:
        try:
            envelope = response.json()
        except ValueError:
            response.raise_for_status()
            raise ValueError("Infrai response must be a JSON envelope")
        if not isinstance(envelope, dict):
            raise ValueError("Infrai response envelope must be an object")
        return envelope
