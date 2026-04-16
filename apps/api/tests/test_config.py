import importlib
import os
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))


class SettingsTests(unittest.TestCase):
    tracked_env_keys = ("APP_NAME", "APP_ENV", "LOG_LEVEL")

    def tearDown(self) -> None:
        self._reload_config({})

    def _reload_config(self, env_updates: dict[str, str]):
        with patch.dict(os.environ, env_updates, clear=False):
            if not env_updates:
                for key in self.tracked_env_keys:
                    os.environ.pop(key, None)

            module = importlib.import_module("app.core.config")
            return importlib.reload(module)

    def test_settings_use_defaults_when_env_vars_are_missing(self) -> None:
        config = self._reload_config({})

        self.assertEqual(config.settings.app_name, "avatar-api")
        self.assertEqual(config.settings.app_env, "development")
        self.assertEqual(config.settings.log_level, "info")

    def test_settings_read_values_from_environment(self) -> None:
        config = self._reload_config(
            {
                "APP_NAME": "test-avatar",
                "APP_ENV": "test",
                "LOG_LEVEL": "debug",
            }
        )

        self.assertEqual(config.settings.app_name, "test-avatar")
        self.assertEqual(config.settings.app_env, "test")
        self.assertEqual(config.settings.log_level, "debug")

    def test_settings_dataclass_is_frozen(self) -> None:
        config = self._reload_config({})

        with self.assertRaises(FrozenInstanceError):
            config.settings.app_name = "mutated"


if __name__ == "__main__":
    unittest.main()
