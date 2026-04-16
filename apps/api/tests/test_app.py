"""Tests for app-level concerns: FastAPI metadata, OpenAPI schema, routing table."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))

try:
    from app.main import app
    _DEPS_AVAILABLE = True
except ModuleNotFoundError:
    _DEPS_AVAILABLE = False

_DB_OK = (True, "127.0.0.1:5432")


@unittest.skipUnless(_DEPS_AVAILABLE, "fastapi not installed")
class TestAppMetadata(unittest.TestCase):
    def test_app_title(self) -> None:
        self.assertEqual(app.title, "avatar-api")

    def test_app_version(self) -> None:
        self.assertEqual(app.version, "0.1.0")

    def test_openapi_schema_is_dict(self) -> None:
        self.assertIsInstance(app.openapi(), dict)

    def test_openapi_info_title(self) -> None:
        self.assertEqual(app.openapi()["info"]["title"], "avatar-api")

    def test_openapi_info_version(self) -> None:
        self.assertEqual(app.openapi()["info"]["version"], "0.1.0")

    def test_health_path_in_openapi(self) -> None:
        self.assertIn("/api/v1/health", app.openapi()["paths"])

    def test_health_path_has_get_operation(self) -> None:
        self.assertIn("get", app.openapi()["paths"]["/api/v1/health"])

    def test_router_prefix_is_api_v1(self) -> None:
        routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
        self.assertTrue(any("/api/v1/health" in p for p in routes))

    def test_app_has_middleware(self) -> None:
        self.assertGreater(len(app.user_middleware), 0)


@unittest.skipUnless(_DEPS_AVAILABLE, "fastapi not installed")
class TestAppRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient
        cls._db_patcher = patch("app.api.v1.routes_health.check_db_tcp", return_value=_DB_OK)
        cls._db_patcher.start()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._db_patcher.stop()

    def test_unknown_route_returns_404(self) -> None:
        self.assertEqual(self.client.get("/does-not-exist").status_code, 404)

    def test_root_returns_404(self) -> None:
        self.assertEqual(self.client.get("/").status_code, 404)

    def test_api_v1_prefix_without_trailing_path(self) -> None:
        r = self.client.get("/api/v1", follow_redirects=False)
        self.assertIn(r.status_code, (404, 307, 308))

    def test_health_route_accessible(self) -> None:
        self.assertEqual(self.client.get("/api/v1/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
