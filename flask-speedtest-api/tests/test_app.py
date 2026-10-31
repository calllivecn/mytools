import io
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import CHUNK_SIZE, MB, create_app  # noqa: E402


class SpeedTestApiTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(prefix="", max_upload_mb=0)
        self.client = self.app.test_client()

    def test_upload_discards_raw_body(self):
        payload = os.urandom(300_000)
        response = self.client.post(
            "/api/upload", data=payload, content_type="application/octet-stream"
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["filename"], "upload.bin")
        self.assertEqual(body["received_bytes"], len(payload))

    def test_upload_multipart_body(self):
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b"x" * 1024), "test.bin")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        # The multipart envelope is counted as well; nothing is stored.
        self.assertGreaterEqual(response.get_json()["received_bytes"], 1024)

    def test_upload_empty_body(self):
        response = self.client.post("/api/upload", data=b"")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["received_bytes"], 0)

    def test_download_with_size(self):
        response = self.client.get("/api/download?size=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2 * MB)
        self.assertEqual(response.headers["Content-Length"], str(2 * MB))
        self.assertEqual(response.headers["X-Download-Bytes"], str(2 * MB))
        self.assertEqual(response.mimetype, "application/octet-stream")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(
            response.headers["Content-Disposition"],
            'attachment; filename="speedtest.bin"; '
            "filename*=UTF-8''speedtest.bin",
        )

    def test_download_fractional_size(self):
        response = self.client.get("/api/download?size=0.5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), MB // 2)

    def test_download_without_size_is_endless(self):
        response = self.client.get("/api/download", buffered=False)
        try:
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("Content-Length", response.headers)
            self.assertEqual(response.headers["X-Download-Bytes"], "unlimited")

            total = 0
            for chunk in response.response:
                total += len(chunk)
                if total >= 3 * CHUNK_SIZE:
                    break
            self.assertGreaterEqual(total, 3 * CHUNK_SIZE)
        finally:
            response.close()

    def test_head_download_with_size(self):
        response = self.client.head("/api/download?size=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Length"], str(MB))
        self.assertEqual(response.data, b"")

    def test_download_invalid_size(self):
        for size in ("0", "-1", "abc", "1e999999"):
            response = self.client.get("/api/download", query_string={"size": size})
            self.assertEqual(response.status_code, 400, size)
            self.assertFalse(response.get_json()["ok"])

    def test_empty_size_means_endless(self):
        response = self.client.get(
            "/api/download", query_string={"size": ""}, buffered=False
        )
        try:
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("Content-Length", response.headers)
        finally:
            response.close()

    def test_upload_too_large(self):
        app = create_app(prefix="", max_upload_mb=1)
        client = app.test_client()
        response = client.post(
            "/api/upload", data=b"x" * (2 * MB), content_type="application/octet-stream"
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.get_json()["max_upload_mb"], 1)

    def test_prefix(self):
        app = create_app(prefix="speedtest", max_upload_mb=0)
        client = app.test_client()

        response = client.get("/speedtest/")
        self.assertEqual(response.status_code, 200)
        endpoints = response.get_json()["endpoints"]
        self.assertEqual(endpoints["upload"], "/speedtest/api/upload")
        self.assertEqual(
            endpoints["download"], "/speedtest/api/download?size=<MB>"
        )

        response = client.post(
            "/speedtest/api/upload", data=b"abc", content_type="application/octet-stream"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["received_bytes"], 3)

        response = client.get("/speedtest/api/download?size=0.1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), MB // 10)

        # The API is not reachable without the configured prefix.
        self.assertEqual(client.get("/api/download?size=1").status_code, 404)

    def test_prefix_normalization(self):
        app = create_app(prefix="/speedtest/", max_upload_mb=0)
        client = app.test_client()
        self.assertEqual(client.get("/speedtest/").status_code, 200)
        self.assertEqual(client.get("/speedtest/api/download?size=0.1").status_code, 200)


if __name__ == "__main__":
    unittest.main()
