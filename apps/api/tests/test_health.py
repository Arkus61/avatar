import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.responses import Response
from fastapi.testclient import TestClient

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))

from app.api.v1 import routes_health
from app.main import app, trace_context_middleware


class HealthEndpointTests(unittest.TestCase):
    def test_health_endpoint_returns_expected_envelope(self) -> None:
        fixed_now = datetime(2026, 4, 16, 12, 0, tzinfo=timezone.utc)

        with (
            patch("app.api.v1.routes_health.check_db_tcp", return_value=(True, "db.internal:5432")) as check_db_tcp,
            patch("app.api.v1.routes_health.datetime") as mock_datetime,
            patch("app.main.uuid4", return_value="trace-123"),
            patch("builtins.print") as mock_print,
        ):
            mock_datetime.now.return_value = fixed_now
            client = TestClient(app)
            response = client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Trace-Id"], "trace-123")
        self.assertEqual(app.title, "avatar-api")
        self.assertEqual(app.version, "0.1.0")

        payload = response.json()
        self.assertEqual(payload["data"], {"status": "ok"})
        self.assertEqual(
            payload["meta"],
            {
                "checked_at": fixed_now.isoformat(),
                "trace_id": "trace-123",
                "db_tcp": {"ok": True, "target": "db.internal:5432"},
            },
        )

        check_db_tcp.assert_called_once_with()
        mock_datetime.now.assert_called_once_with(timezone.utc)
        mock_print.assert_called_once_with("[trace_id=trace-123] GET /api/v1/health")


class HealthFunctionTests(unittest.TestCase):
    def test_health_function_uses_unknown_trace_id_without_middleware(self) -> None:
        fixed_now = datetime(2026, 4, 16, 13, 0, tzinfo=timezone.utc)
        request = SimpleNamespace(state=SimpleNamespace())

        with (
            patch.object(routes_health, "check_db_tcp", return_value=(False, "127.0.0.1:5432")) as check_db_tcp,
            patch.object(routes_health, "datetime") as mock_datetime,
        ):
            mock_datetime.now.return_value = fixed_now
            payload = routes_health.health(request)

        self.assertEqual(
            payload,
            {
                "data": {"status": "ok"},
                "meta": {
                    "checked_at": fixed_now.isoformat(),
                    "trace_id": "unknown",
                    "db_tcp": {"ok": False, "target": "127.0.0.1:5432"},
                },
            },
        )
        check_db_tcp.assert_called_once_with()
        mock_datetime.now.assert_called_once_with(timezone.utc)


class TraceContextMiddlewareTests(unittest.IsolatedAsyncioTestCase):
    async def test_trace_context_middleware_sets_request_state_and_response_header(self) -> None:
        request = SimpleNamespace(
            method="POST",
            url=SimpleNamespace(path="/probe"),
            state=SimpleNamespace(),
        )
        observed = {}

        async def call_next(incoming_request):
            observed["trace_id"] = incoming_request.state.trace_id
            return Response("ok", media_type="text/plain")

        with (
            patch("app.main.uuid4", return_value="trace-456"),
            patch("builtins.print") as mock_print,
        ):
            response = await trace_context_middleware(request, call_next)

        self.assertEqual(request.state.trace_id, "trace-456")
        self.assertEqual(observed["trace_id"], "trace-456")
        self.assertEqual(response.headers["X-Trace-Id"], "trace-456")
        mock_print.assert_called_once_with("[trace_id=trace-456] POST /probe")


if __name__ == "__main__":
    unittest.main()
