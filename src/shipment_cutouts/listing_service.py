from fastapi import FastAPI, HTTPException

from .background_client import BackgroundClient, InfraiError
from .listing_workflow import prepare_listing
from .shipment_models import ListingCutoutRequest, ListingCutoutResult

service = FastAPI(title="Shipment listing cutouts")


@service.post("/listing-cutouts", response_model=ListingCutoutResult)
async def create_listing_cutout(request: ListingCutoutRequest) -> ListingCutoutResult:
    try:
        return await prepare_listing(request, BackgroundClient())
    except InfraiError as exc:
        status_code = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "upstream": exc.detail},
        ) from exc

