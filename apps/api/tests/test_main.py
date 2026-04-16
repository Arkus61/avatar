"""Tests for ``app.main``.

Covers the FastAPI application bootstrap and the ``trace_context_middleware``:

* Correct app metadata (title/version).
* Health router mounted under the ``/api/v1`` prefix.
* Middleware sets ``request.state.trace_id`` and emits the
  ``X-Trace-Id`` response header.
* Trace IDs differ across requests.
* The middleware logs a deterministic line containing the trace id.
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    FastAPI = None  # type: ignore[assignment]
    TestClient = None  # type: ignore[assignment]

try:
    from app.main import app
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    app = None  # type: ignore[assignment]


@unittest.skipIf(
    TestClient is None or app is None,
    "fastapi dependency is not installed in this environment",
)
class ApplicationBootstrapTests(unittest.TestCase):
    def test_app_is_fastapi_instance_with_expected_metadata(self) -> None:
        assert FastAPI is not None and app is not None
        self.assertIsInstance(app, FastAPI)
        self.assertEqual(app.title, "avatar-api")
        self.assertEqual(app.version, "0.1.0")

    def test_health_router_mounted_under_v1_prefix(self) -> None:
        assert app is not None
        paths = {route.path for route in app.routes}
        self.assertIn("/api/v1/health", paths)


@unittest.skipIf(
    TestClient is None or app is None,
    "fastapi dependency is not installed in this environment",
)
class TraceContextMiddlewareTests(unittest.TestCase):
    def setUp(self) -> None:
        assert TestClient is not None and app is not None
        self.client = TestClient(app)

    def test_middleware_sets_trace_id_header(self) -> None:
        response = self.client.get("/api/v1/health")

        self.assertIn("X-Trace-Id", response.headers)
        self.assertTrue(response.headers["X-Trace-Id"])

    def test_trace_id_differs_per_request(self) -> None:
        first = self.client.get("/api/v1/health").headers["X-Trace-Id"]
        second = self.client.get("/api/v1/health").headers["X-Trace-Id"]

        self.assertNotEqual(first, second)

    def test_trace_id_is_logged_with_method_and_path(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            response = self.client.get("/api/v1/health")

        trace_id = response.headers["X-Trace-Id"]
        logged = buffer.getvalue()
        self.assertIn(f"[trace_id={trace_id}]", logged)
        self.assertIn("GET /api/v1/health", logged)

    def test_trace_id_header_present_on_404(self) -> None:
        response = self.client.get("/api/v1/does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertIn("X-Trace-Id", response.headers)

    def test_trace_id_uses_generated_uuid(self) -> None:
        import app.main as main_module

        with mock.patch.object(main_module, "uuid4", return_value="deadbeef-dead-4beef-dead-beefdeadbeef"):
            response = self.client.get("/api/v1/health")

        self.assertEqual(response.headers["X-Trace-Id"], "deadbeef-dead-4beef-dead-beefdeadbeef")

    def test_trace_id_in_response_matches_request_state(self) -> None:
        """``request.state.trace_id`` should feed the response header verbatim.

        We verify this by inspecting the JSON body which surfaces the trace
        id from the middleware via ``request.state``.
        """
        response = self.client.get("/api/v1/health")

        self.assertEqual(
            response.headers["X-Trace-Id"],
            response.json()["meta"]["trace_id"],
        )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    unittest.main()
