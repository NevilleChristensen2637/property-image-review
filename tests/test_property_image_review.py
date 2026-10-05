import base64
import json
from unittest.mock import patch

from src.property_image_review import InfraiImageClient, decide_publication


def test_upload_sends_json_file_and_filename() -> None:
    class Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'{"ok": true, "data": {"filename": "inspection.jpg"}}'

    with patch("src.property_image_review.urllib.request.urlopen", return_value=Response()) as urlopen:
        result = InfraiImageClient(api_key="test").upload(b"\x00\xff", "inspection.jpg")

    request = urlopen.call_args.args[0]
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data) == {
        "file": base64.b64encode(b"\x00\xff").decode("ascii"),
        "filename": "inspection.jpg",
    }
    assert result == {"filename": "inspection.jpg"}


def test_tenant_documents_are_not_published_even_when_clean() -> None:
    result = decide_publication("tenant_document", "lease-scan.jpg", False)
    assert result.publish is False
    assert "private" in result.reason


def test_clean_inspection_image_can_be_published() -> None:
    result = decide_publication("inspection", "boiler-room.jpg", False)
    assert result.publish is True
