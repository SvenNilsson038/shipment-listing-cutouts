import argparse
import asyncio
import base64
import json
from datetime import UTC, datetime

import httpx

from shipment_cutouts.background_client import BackgroundClient
from shipment_cutouts.listing_workflow import prepare_listing
from shipment_cutouts.shipment_models import (
    EventKind,
    ImageReference,
    ListingCutoutRequest,
    ProofOfDelivery,
    ShipmentEvent,
)


async def run(image: str) -> None:
    now = datetime.now(UTC)
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(image)
        response.raise_for_status()
    request = ListingCutoutRequest(
        shipment_id="SHP-1042",
        image=ImageReference(base64=base64.b64encode(response.content).decode("ascii")),
        events=[ShipmentEvent(kind=EventKind.DELIVERED, occurred_at=now)],
        proof_of_delivery=ProofOfDelivery(
            filename="pod-SHP-1042.jpg",
            media_type="image/jpeg",
            signed_at=now,
        ),
    )
    result = await prepare_listing(request, BackgroundClient())
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare one shipment listing photo")
    parser.add_argument("image", help="Public image URL")
    arguments = parser.parse_args()
    asyncio.run(run(arguments.image))
