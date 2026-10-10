from typing import Protocol

from .shipment_models import ListingCutoutRequest, ListingCutoutResult


class CutoutProcessor(Protocol):
    async def remove(
        self, image: dict[str, str], output_format: str, idempotency_key: str
    ) -> dict[str, object]:
        """Return processed image data for one listing photo."""


async def prepare_listing(
    request: ListingCutoutRequest, processor: CutoutProcessor
) -> ListingCutoutResult:
    unresolved = [item for item in request.exceptions if not item.resolved]
    if unresolved:
        return ListingCutoutResult(
            shipment_id=request.shipment_id,
            state="needs_review",
            reason=f"{len(unresolved)} unresolved shipment exception(s)",
        )

    latest_event = max(request.events, key=lambda event: event.occurred_at)
    idempotency_key = f"listing-cutout:{request.shipment_id}:{latest_event.occurred_at.isoformat()}"
    cutout = await processor.remove(request.image.model_dump(), request.format, idempotency_key)
    return ListingCutoutResult(
        shipment_id=request.shipment_id,
        state="ready_for_listing",
        cutout=cutout,
    )
