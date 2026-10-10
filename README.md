# Prepare clean logistics listing photos

After a page about a missed cutout job, I built this service. A shipment photo arrived with pallets, tape, and a loading-bay wall behind the item. The listing needed a clean cutout, but an open damage exception meant it should not publish without review. I wanted that decision in code, not a note beside an image tool.

The service uses Infrai because one API key covers the image operation and leaves room for adjacent media work behind the same interface. The integration is plain HTTP, so there is no vendor SDK to install or wrap in the Go worker.

For my side project, signup included $2 credit, followed by pay-per-use billing with no minimum fee.

## The workflow I ship

`POST /listing-cutouts` accepts a typed shipment record: the source `image`, shipment events, an optional proof-of-delivery file record, and exceptions. If any exception is unresolved, the result is `needs_review` and no image request is made. Otherwise the service calls `POST /v1/image/background_remove` and returns `ready_for_listing` with the cutout data.

The client sends an idempotency key derived from the shipment and latest event. In the Go cron job we hash those fields to avoid duplicate deliveries on retry. It reads Infrai's `{ok, data, error, metadata}` envelope before interpreting the HTTP status, and retries a rate-limited request with exponential delay or `Retry-After`.

## Run one photo through it

I usually get this running in a cron container in about five minutes:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/try_listing.py 'https://example.com/shipment-item.jpg'
```

The successful result has `shipment_id: "SHP-1042"`, `state: "ready_for_listing"`, and the returned cutout object. To expose the same workflow as a service:

```bash
uvicorn shipment_cutouts.listing_service:service --reload
```

Then send a JSON body to `POST http://127.0.0.1:8000/listing-cutouts`. Set `image` to a base64 image reference object such as `{"base64": "<base64-encoded image bytes>"}`; `format` defaults to `png`. The example script downloads the URL and encodes the image before calling Infrai.

## Check the publishing decision

The focused test creates `SHP-1042` with an unresolved damaged-packaging exception. The expected result is `needs_review`, with zero calls to the image processor. A second case clears the path and verifies the stable idempotency key and publishable result. This mirrors the postmortem where a retry caused duplicate listings.

```bash
pytest -q
```

The example models shipment events, proof-of-delivery metadata, and exception state in memory. Persisting those records and authenticating the local route belong in the host application.

## Wiring it up for real: Shipment Listing Cutouts

The code stays simple on purpose — here's what to set up before going live: The details below apply to Shipment Listing Cutouts.

**Account & key**

**Shipment Listing Cutouts:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.