"""Tests for ``app.api.v1.routes_health``.

Covers the health endpoint envelope:

* HTTP 200 with the ``{"data": ..., "meta": ...}`` envelope.
* ``data.status == "ok"``.
* ``meta.checked_at`` is a valid ISO-8601 UTC timestamp.
* ``meta.trace_id`` is propagated from the middleware and mirrored into
  the response ``X-Trace-Id`` header.
* ``meta.db_tcp`` reflects the outcome of the underlying TCP probe for
  both success and failure branches.
* Router configuration (prefix/tag) behaves as wired in ``main.py``.
"""

from __future__ import annotations

import re
import unittest
from datetime import datetime
from unittest import mock

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    TestClient = None  # type: ignore[assignment]

try:
    from app.main import app
    from app.api.v1 import routes_health
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    app = None  # type: ignore[assignment]
    routes_health = None  # type: ignore[assignment]


ISO_UTC_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$"
)
UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@unittest.skipIf(
    TestClient is None or app is None,
    "fastapi dependency is not installed in this environment",
)
class HealthRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        assert TestClient is not None and app is not None
        self.client = TestClient(app)

    def test_health_endpoint_returns_success_envelope(self) -> None:
        with mock.patch.object(routes_health, "check_db_tcp", return_value=(True, "127.0.0.1:5432")):
            response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("data", payload)
        self.assertIn("meta", payload)
        self.assertEqual(payload["data"], {"status": "ok"})

    def test_meta_contains_iso_utc_timestamp(self) -> None:
        with mock.patch.object(routes_health, "check_db_tcp", return_value=(True, "127.0.0.1:5432")):
            response = self.client.get("/api/v1/health")

        checked_at = response.json()["meta"]["checked_at"]
        self.assertRegex(checked_at, ISO_UTC_PATTERN)

        parsed = datetime.fromisoformat(checked_at)
        self.assertIsNotNone(parsed.tzinfo)

    def test_trace_id_is_propagated_to_meta_and_header(self) -> None:
        with mock.patch.object(routes_health, "check_db_tcp", return_value=(True, "127.0.0.1:5432")):
            response = self.client.get("/api/v1/health")

        trace_id = response.json()["meta"]["trace_id"]
        self.assertRegex(trace_id, UUID4_PATTERN)
        self.assertEqual(response.headers.get("X-Trace-Id"), trace_id)

    def test_each_request_gets_a_unique_trace_id(self) -> None:
        with mock.patch.object(routes_health, "check_db_tcp", return_value=(True, "127.0.0.1:5432")):
            first = self.client.get("/api/v1/health").json()["meta"]["trace_id"]
            second = self.client.get("/api/v1/health").json()["meta"]["trace_id"]

        self.assertNotEqual(first, second)

    def test_db_tcp_reports_success(self) -> None:
        with mock.patch.object(routes_health, "check_db_tcp", return_value=(True, "db:5432")):
            response = self.client.get("/api/v1/health")

        db_tcp = response.json()["meta"]["db_tcp"]
        self.assertEqual(db_tcp, {"ok": True, "target": "db:5432"})

    def test_db_tcp_reports_failure(self) -> None:
        with mock.patch.object(routes_health, "check_db_tcp", return_value=(False, "db:5432")):
            response = self.client.get("/api/v1/health")

        db_tcp = response.json()["meta"]["db_tcp"]
        self.assertEqual(db_tcp, {"ok": False, "target": "db:5432"})

    def test_unknown_route_returns_404(self) -> None:
        response = self.client.get("/api/v1/does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertIn("X-Trace-Id", response.headers)

    def test_router_is_tagged_health(self) -> None:
        assert routes_health is not None
        self.assertIn("health", routes_health.router.tags)

    def test_health_route_is_registered_under_v1_prefix(self) -> None:
        assert app is not None
        paths = {route.path for route in app.routes}
        self.assertIn("/api/v1/health", paths)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    unittest.main()
