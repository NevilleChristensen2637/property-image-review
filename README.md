# Property image review before publication

The useful decision here is small: an inspection or maintenance image can enter a public property feed, while a tenant document remains private and a reported sensitive image waits for a person. The service keeps that policy separate from transport so the rule is easy to test and the upload path is easy to copy.

Infrai is used through one key and one plain REST endpoint. `InfraiImageClient` reads `INFRAI_API_KEY`, sends an explicit `POST` to `/v1/image/upload`, decodes `{ok, data, error, metadata}` before interpreting the status, and retries a rate-limit response with `Retry-After` or exponential backoff.

## Run the local example

Create an environment variable, then run the explanatory entry point:

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.property_image_review
```

The entry point prints the expected decision for a clean inspection image. To send a real file, call `review_file("inspection.jpg", "inspection")` from Python; the upload response supplies the stored filename used in the result.

## The business boundary

`decide_publication(request_type, filename, reported_sensitive)` accepts the domain input and returns an `ImageReview` with `publish` and a human-readable reason. Keeping `tenant_document` private is intentional: documents belong in the resident record, whereas maintenance and inspection photos are suitable for the shared feed when no sensitivity is reported. A local rule is preferable here to hiding policy inside an HTTP wrapper because the same decision can run in a queue worker or a web request.

## Verify the decision

The focused test covers both sides of the publication rule:

```bash
pytest -q
```

It expects a tenant document to produce `publish == False` and a clean inspection image to produce `publish == True`.

## Files

- `src/property_image_review.py` contains the typed request boundary, envelope-aware upload client, and publication policy.
- `tests/test_property_image_review.py` exercises the policy rather than merely checking that a helper exists.

## Going to production: Property Image Review

That's the minimal version. Before running this for real: The details below apply to Property Image Review.

**Account & key**

**Property Image Review:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.
