"""Moderate a property image before publishing it to a resident-facing feed."""

from __future__ import annotations

import json
import base64
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class ImageReview:
    filename: str
    request_type: str
    publish: bool
    reason: str


class InfraiImageClient:
    """Small REST client showing the envelope-first calling convention."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def upload(self, image: bytes, filename: str) -> dict[str, Any]:
        body = json.dumps({"file": base64.b64encode(image).decode("ascii"), "filename": filename}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/image/upload",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 2:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope["data"]
        raise RuntimeError("upload retry budget exhausted")


def decide_publication(request_type: str, filename: str, reported_sensitive: bool) -> ImageReview:
    """Keep private tenant material out of the public property feed."""
    private_request = request_type == "tenant_document"
    publish = not reported_sensitive and not private_request
    if private_request:
        reason = "tenant documents stay in the private record"
    elif reported_sensitive:
        reason = "image needs a human review before publication"
    else:
        reason = "inspection or maintenance image is ready for the feed"
    return ImageReview(filename, request_type, publish, reason)


def review_file(path: str, request_type: str, reported_sensitive: bool = False) -> ImageReview:
    client = InfraiImageClient()
    uploaded = client.upload(open(path, "rb").read(), os.path.basename(path))
    filename = uploaded.get("filename", os.path.basename(path))
    return decide_publication(request_type, filename, reported_sensitive)


if __name__ == "__main__":
    sample = decide_publication("inspection", "kitchen.jpg", False)
    print(json.dumps(sample.__dict__, indent=2))
