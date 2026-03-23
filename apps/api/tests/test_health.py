import unittest
import sys
from pathlib import Path

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    TestClient = None  # type: ignore[assignment]

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))

try:
    from app.main import app
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    app = None  # type: ignore[assignment]


class HealthRouteTests(unittest.TestCase):
    @unittest.skipIf(
        TestClient is None or app is None,
        "fastapi dependency is not installed in this environment",
    )
    def test_health_endpoint_returns_success_envelope(self) -> None:
        assert TestClient is not None and app is not None
        client = TestClient(app)
        response = client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("data", payload)
        self.assertIn("meta", payload)
        self.assertEqual(payload["data"]["status"], "ok")
        self.assertIn("checked_at", payload["meta"])
        self.assertIn("trace_id", payload["meta"])
        self.assertIn("db_tcp", payload["meta"])


if __name__ == "__main__":
    unittest.main()
