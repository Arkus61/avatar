"""Tests for the trace_context_middleware in app.main."""
import sys
import re
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))

try:
    from fastapi.testclient import TestClient
    from app.main import app
    _DEPS_AVAILABLE = True
except ModuleNotFoundError:
    _DEPS_AVAILABLE = False

UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)

_DB_OK = (True, "127.0.0.1:5432")


@unittest.skipUnless(_DEPS_AVAILABLE, "fastapi not installed")
class TestTraceContextMiddleware(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._db_patcher = patch("app.api.v1.routes_health.check_db_tcp", return_value=_DB_OK)
        cls._db_patcher.start()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._db_patcher.stop()

    def test_x_trace_id_header_present(self) -> None:
        r = self.client.get("/api/v1/health")
        self.assertIn("x-trace-id", r.headers)

    def test_x_trace_id_is_valid_uuid4(self) -> None:
        trace_id = self.client.get("/api/v1/health").headers["x-trace-id"]
        self.assertRegex(trace_id, UUID4_PATTERN)

    def test_x_trace_id_unique_per_request(self) -> None:
        ids = {self.client.get("/api/v1/health").headers["x-trace-id"] for _ in range(5)}
        self.assertEqual(len(ids), 5)

    def test_trace_id_propagated_to_response_body(self) -> None:
        r = self.client.get("/api/v1/health")
        self.assertEqual(r.headers["x-trace-id"], r.json()["meta"]["trace_id"])

    def test_middleware_does_not_break_non_health_routes(self) -> None:
        r = self.client.get("/nonexistent-route")
        self.assertIn("x-trace-id", r.headers)
        self.assertEqual(r.status_code, 404)

    def test_middleware_present_on_post_request(self) -> None:
        r = self.client.post("/api/v1/health")
        self.assertIn("x-trace-id", r.headers)

    def test_uuid_generated_via_uuid4(self) -> None:
        """Middleware must call uuid4 for every request."""
        captured = []
        original_uuid4 = __import__("uuid").uuid4

        def capturing_uuid4():
            val = original_uuid4()
            captured.append(str(val))
            return val

        with patch("app.main.uuid4", side_effect=capturing_uuid4):
            r = self.client.get("/api/v1/health")

        self.assertTrue(len(captured) >= 1)
        self.assertEqual(r.headers["x-trace-id"], captured[-1])

    def test_trace_id_in_header_matches_body_on_second_request(self) -> None:
        for _ in range(3):
            r = self.client.get("/api/v1/health")
            self.assertEqual(r.headers["x-trace-id"], r.json()["meta"]["trace_id"])


if __name__ == "__main__":
    unittest.main()
