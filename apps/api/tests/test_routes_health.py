"""Tests for app.api.v1.routes_health — /api/v1/health endpoint."""
import sys
import unittest
from datetime import datetime, timezone
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

_DB_OK = (True, "127.0.0.1:5432")
_DB_FAIL = (False, "127.0.0.1:5432")


def _patch_db(return_value=_DB_OK):
    """Patch check_db_tcp at the routes module (used by the handler)."""
    return patch("app.api.v1.routes_health.check_db_tcp", return_value=return_value)


@unittest.skipUnless(_DEPS_AVAILABLE, "fastapi not installed")
class TestHealthRouteDbOk(unittest.TestCase):
    """Tests with DB TCP reporting success."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._patcher = _patch_db(_DB_OK)
        cls._patcher.start()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._patcher.stop()

    def _get(self):
        return self.client.get("/api/v1/health")

    # ---- HTTP basics --------------------------------------------------------

    def test_status_code_200(self) -> None:
        self.assertEqual(self._get().status_code, 200)

    def test_content_type_json(self) -> None:
        ct = self._get().headers.get("content-type", "")
        self.assertIn("application/json", ct)

    def test_method_not_allowed_post(self) -> None:
        self.assertEqual(self.client.post("/api/v1/health").status_code, 405)

    def test_method_not_allowed_delete(self) -> None:
        self.assertEqual(self.client.delete("/api/v1/health").status_code, 405)

    # ---- Envelope structure -------------------------------------------------

    def test_envelope_has_data_key(self) -> None:
        self.assertIn("data", self._get().json())

    def test_envelope_has_meta_key(self) -> None:
        self.assertIn("meta", self._get().json())

    def test_data_status_is_ok(self) -> None:
        self.assertEqual(self._get().json()["data"]["status"], "ok")

    def test_meta_has_checked_at(self) -> None:
        self.assertIn("checked_at", self._get().json()["meta"])

    def test_meta_has_trace_id(self) -> None:
        self.assertIn("trace_id", self._get().json()["meta"])

    def test_meta_has_db_tcp(self) -> None:
        self.assertIn("db_tcp", self._get().json()["meta"])

    def test_db_tcp_has_ok_field(self) -> None:
        self.assertIn("ok", self._get().json()["meta"]["db_tcp"])

    def test_db_tcp_has_target_field(self) -> None:
        self.assertIn("target", self._get().json()["meta"]["db_tcp"])

    # ---- DB tcp state: connected ---------------------------------------------

    def test_db_tcp_ok_true_when_connected(self) -> None:
        self.assertTrue(self._get().json()["meta"]["db_tcp"]["ok"])

    def test_db_tcp_target_is_string(self) -> None:
        self.assertIsInstance(self._get().json()["meta"]["db_tcp"]["target"], str)

    def test_db_tcp_target_contains_port(self) -> None:
        self.assertIn(":", self._get().json()["meta"]["db_tcp"]["target"])

    # ---- Timestamps ----------------------------------------------------------

    def test_checked_at_is_iso8601(self) -> None:
        ts = self._get().json()["meta"]["checked_at"]
        self.assertIsInstance(datetime.fromisoformat(ts), datetime)

    def test_checked_at_is_utc(self) -> None:
        ts = self._get().json()["meta"]["checked_at"]
        parsed = datetime.fromisoformat(ts)
        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.utcoffset().total_seconds(), 0)  # type: ignore[union-attr]

    # ---- Trace ID -----------------------------------------------------------

    def test_trace_id_not_unknown_when_middleware_active(self) -> None:
        self.assertNotEqual(self._get().json()["meta"]["trace_id"], "unknown")

    # ---- OpenAPI tag --------------------------------------------------------

    def test_health_route_tagged_health(self) -> None:
        schema = app.openapi()
        tags = schema["paths"].get("/api/v1/health", {}).get("get", {}).get("tags", [])
        self.assertIn("health", tags)


@unittest.skipUnless(_DEPS_AVAILABLE, "fastapi not installed")
class TestHealthRouteDbFail(unittest.TestCase):
    """Tests with DB TCP reporting failure."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._patcher = _patch_db(_DB_FAIL)
        cls._patcher.start()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._patcher.stop()

    def test_db_tcp_ok_false_when_refused(self) -> None:
        body = self.client.get("/api/v1/health").json()
        self.assertFalse(body["meta"]["db_tcp"]["ok"])

    def test_status_still_200_when_db_unreachable(self) -> None:
        self.assertEqual(self.client.get("/api/v1/health").status_code, 200)

    def test_data_status_still_ok_when_db_unreachable(self) -> None:
        body = self.client.get("/api/v1/health").json()
        self.assertEqual(body["data"]["status"], "ok")


@unittest.skipUnless(_DEPS_AVAILABLE, "fastapi not installed")
class TestHealthHandlerDirectly(unittest.TestCase):
    """Unit-tests the route handler function directly without HTTP stack."""

    def test_trace_id_fallback_is_unknown_without_middleware(self) -> None:
        from fastapi import Request
        from app.api.v1.routes_health import health as handler

        scope = {"type": "http", "method": "GET", "path": "/api/v1/health",
                 "headers": [], "query_string": b""}
        with patch("app.api.v1.routes_health.check_db_tcp", return_value=_DB_OK):
            result = handler(Request(scope))
        self.assertEqual(result["meta"]["trace_id"], "unknown")

    def test_handler_returns_dict(self) -> None:
        from fastapi import Request
        from app.api.v1.routes_health import health as handler

        scope = {"type": "http", "method": "GET", "path": "/api/v1/health",
                 "headers": [], "query_string": b""}
        with patch("app.api.v1.routes_health.check_db_tcp", return_value=_DB_OK):
            result = handler(Request(scope))
        self.assertIsInstance(result, dict)

    def test_handler_calls_check_db_tcp(self) -> None:
        from fastapi import Request
        from app.api.v1.routes_health import health as handler

        scope = {"type": "http", "method": "GET", "path": "/api/v1/health",
                 "headers": [], "query_string": b""}
        with patch("app.api.v1.routes_health.check_db_tcp", return_value=(True, "pg:1234")) as mock_check:
            result = handler(Request(scope))
        mock_check.assert_called_once()
        self.assertEqual(result["meta"]["db_tcp"]["target"], "pg:1234")

    def test_handler_reflects_db_failure(self) -> None:
        from fastapi import Request
        from app.api.v1.routes_health import health as handler

        scope = {"type": "http", "method": "GET", "path": "/api/v1/health",
                 "headers": [], "query_string": b""}
        with patch("app.api.v1.routes_health.check_db_tcp", return_value=(False, "pg:5432")):
            result = handler(Request(scope))
        self.assertFalse(result["meta"]["db_tcp"]["ok"])


if __name__ == "__main__":
    unittest.main()
