import asyncio
from datetime import UTC, datetime

from shipment_cutouts.listing_workflow import prepare_listing
from shipment_cutouts.shipment_models import (
    EventKind,
    ImageReference,
    ListingCutoutRequest,
    ShipmentEvent,
    ShipmentException,
)


class RecordingProcessor:
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, str], str, str]] = []

    async def remove(
        self, image: dict[str, str], output_format: str, idempotency_key: str
    ) -> dict[str, object]:
        self.calls.append((image, output_format, idempotency_key))
        return {"id": "img-cutout-1042", "format": output_format}


def test_open_exception_holds_listing_for_review() -> None:
    processor = RecordingProcessor()
    request = ListingCutoutRequest(
        shipment_id="SHP-1042",
        image=ImageReference(base64="aW1hZ2U="),
        events=[
            ShipmentEvent(
                kind=EventKind.IN_TRANSIT,
                occurred_at=datetime(2026, 9, 5, 8, 30, tzinfo=UTC),
            )
        ],
        exceptions=[
            ShipmentException(
                category="damaged_packaging",
                note="Confirm the item photo before publishing",
            )
        ],
    )

    result = asyncio.run(prepare_listing(request, processor))

    assert result.state == "needs_review"
    assert result.reason == "1 unresolved shipment exception(s)"
    assert processor.calls == []


def test_clear_shipment_produces_a_publishable_cutout() -> None:
    processor = RecordingProcessor()
    request = ListingCutoutRequest(
        shipment_id="SHP-1042",
        image=ImageReference(base64="aW1hZ2U="),
        format="png",
        events=[
            ShipmentEvent(
                kind=EventKind.LISTING_PHOTO_RECEIVED,
                occurred_at=datetime(2026, 9, 5, 9, 0, tzinfo=UTC),
            )
        ],
    )

    result = asyncio.run(prepare_listing(request, processor))

    assert result.state == "ready_for_listing"
    assert result.cutout == {"id": "img-cutout-1042", "format": "png"}
    assert processor.calls[0][0] == {"base64": "aW1hZ2U="}
    assert processor.calls[0][2] == "listing-cutout:SHP-1042:2026-09-05T09:00:00+00:00"
