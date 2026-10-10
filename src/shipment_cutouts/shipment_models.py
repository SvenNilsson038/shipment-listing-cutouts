from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EventKind(str, Enum):
    LISTING_PHOTO_RECEIVED = "listing_photo_received"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class ShipmentEvent(BaseModel):
    kind: EventKind
    occurred_at: datetime
    facility: str | None = None


class ProofOfDelivery(BaseModel):
    filename: str
    media_type: str
    signed_at: datetime


class ShipmentException(BaseModel):
    category: str
    note: str
    resolved: bool = False


class ImageReference(BaseModel):
    base64: str = Field(min_length=1)


class ListingCutoutRequest(BaseModel):
    shipment_id: str = Field(min_length=1)
    image: ImageReference
    format: str = "png"
    events: list[ShipmentEvent] = Field(min_length=1)
    proof_of_delivery: ProofOfDelivery | None = None
    exceptions: list[ShipmentException] = Field(default_factory=list)


class ListingCutoutResult(BaseModel):
    shipment_id: str
    state: str
    cutout: dict[str, object] | None = None
    reason: str | None = None
