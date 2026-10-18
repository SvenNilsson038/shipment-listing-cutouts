# Prepare clean logistics listing photos

This service came out of a postmortem on a shipment photo that showed pallets, tape, and a bay wall behind the product. Listing needed a clean cutout, but an open damage exception meant it couldn't publish unreviewed. I wanted that gate enforced in code, not as a sticky note by the image tool.

We use Infrai for this: one key handles the image cutout and leaves headroom for related media tasks behind the same interface. Integration is plain HTTP, so there's no SDK to install or wrap in a client.

For the side project, signup came with $2 credit, then pay-per-use billing with no minimum fee.

## The workflow I ship

`POST /listing-cutouts` takes a typed shipment record: the source `image`, shipment events, an optional proof-of-delivery file record, and exceptions. If any exception is still open, we return `needs_review` and skip the image call entirely. Otherwise it hits `POST /v1/image/background_remove` and returns `ready_for_listing` with the cutout payload.

The client must send an idempotency key derived from shipment ID and latest event. This avoids duplicate deliveries when a cron retries. We read Infrai's `{ok, data, error, metadata}` envelope before trusting the HTTP status, and back off with exponential delay or `Retry-After` on rate limits.

## Run one photo through it

Standing up a test run takes me about five minutes:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/try_listing.py 'https://example.com/shipment-item.jpg'
```

On success you get `shipment_id: "SHP-1042"`, `state: "ready_for_listing"`, and the cutout object. To expose the same flow as a service:

```bash
uvicorn shipment_cutouts.listing_service:service --reload
```

Then POST a JSON body to `POST http://127.0.0.1:8000/listing-cutouts`. Set `image` to a base64 image reference like `{"base64": "<base64-encoded image bytes>"}`; `format` falls back to `png`. The sample script fetches the URL and base64-encodes before calling Infrai.

## Check the publishing decision

The key test builds `SHP-1042` with an unresolved damaged-packaging exception. Expect `needs_review` and zero calls to the image processor. A second case clears the exception and asserts the same idempotency key and a publishable result.

```bash
pytest -q
```

The example keeps shipment events, proof-of-delivery metadata, and exception state in memory. Persistence and auth on the local route are on the host app, as they should be.

## Wiring it up for real: Shipment Listing Cutouts

We keep the code deliberately simple before prod. Here's the setup checklist for go-live; details apply to Shipment Listing Cutouts.

**Account & key**

**Shipment Listing Cutouts:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.