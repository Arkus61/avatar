"""Tests for app.core.config — Settings dataclass."""
import sys
import os
import unittest
from pathlib import Path

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))


class TestSettings(unittest.TestCase):
    def _fresh_settings(self) -> object:
        """Import Settings fresh (after env vars are set)."""
        import importlib
        import app.core.config as cfg_module
        importlib.reload(cfg_module)
        return cfg_module.Settings()

    def test_defaults(self) -> None:
        for var in ("APP_NAME", "APP_ENV", "LOG_LEVEL"):
            os.environ.pop(var, None)
        s = self._fresh_settings()
        self.assertEqual(s.app_name, "avatar-api")
        self.assertEqual(s.app_env, "development")
        self.assertEqual(s.log_level, "info")

    def test_env_override_app_name(self) -> None:
        os.environ["APP_NAME"] = "my-service"
        try:
            s = self._fresh_settings()
            self.assertEqual(s.app_name, "my-service")
        finally:
            del os.environ["APP_NAME"]

    def test_env_override_app_env(self) -> None:
        os.environ["APP_ENV"] = "production"
        try:
            s = self._fresh_settings()
            self.assertEqual(s.app_env, "production")
        finally:
            del os.environ["APP_ENV"]

    def test_env_override_log_level(self) -> None:
        os.environ["LOG_LEVEL"] = "debug"
        try:
            s = self._fresh_settings()
            self.assertEqual(s.log_level, "debug")
        finally:
            del os.environ["LOG_LEVEL"]

    def test_settings_is_frozen(self) -> None:
        from app.core.config import settings
        with self.assertRaises((AttributeError, TypeError)):
            settings.app_name = "changed"  # type: ignore[misc]

    def test_module_level_settings_singleton(self) -> None:
        from app.core.config import settings as s1
        from app.core.config import settings as s2
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()
