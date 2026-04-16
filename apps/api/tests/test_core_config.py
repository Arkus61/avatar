"""Tests for ``app.core.config.Settings``.

Covers the default values, environment variable overrides, and immutability
guarantees of the frozen dataclass. The ``Settings`` class reads environment
variables at module import time, so each test reimports the module with the
desired environment to exercise the relevant branch.
"""

from __future__ import annotations

import importlib
import os
import unittest
from unittest import mock


class SettingsDefaultsTests(unittest.TestCase):
    def _reload_settings(self) -> object:
        import app.core.config as config_module

        return importlib.reload(config_module)

    def test_defaults_are_applied_when_no_env_vars_set(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in {"APP_NAME", "APP_ENV", "LOG_LEVEL"}}
        with mock.patch.dict(os.environ, env, clear=True):
            module = self._reload_settings()

            self.assertEqual(module.settings.app_name, "avatar-api")
            self.assertEqual(module.settings.app_env, "development")
            self.assertEqual(module.settings.log_level, "info")

    def test_env_vars_override_defaults(self) -> None:
        overrides = {
            "APP_NAME": "avatar-api-test",
            "APP_ENV": "staging",
            "LOG_LEVEL": "debug",
        }
        with mock.patch.dict(os.environ, overrides, clear=False):
            module = self._reload_settings()

            self.assertEqual(module.settings.app_name, "avatar-api-test")
            self.assertEqual(module.settings.app_env, "staging")
            self.assertEqual(module.settings.log_level, "debug")

    def test_settings_instance_is_frozen(self) -> None:
        module = self._reload_settings()

        with self.assertRaises(Exception):
            module.settings.app_name = "mutated"  # type: ignore[misc]

    def test_module_exposes_settings_symbol(self) -> None:
        module = self._reload_settings()

        self.assertTrue(hasattr(module, "settings"))
        self.assertIs(type(module.settings), module.Settings)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    unittest.main()
