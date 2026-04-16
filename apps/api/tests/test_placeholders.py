"""Import-sanity tests for placeholder modules.

Several modules in the ``app`` package are intentional placeholders today
(``core.exceptions``, ``core.middleware``, ``core.security``, ``core.logging``,
``db.base``, ``db.session``, ``domains``, ``policies``, ``repositories``).
They currently contain only comments, but we still exercise their import
paths so that regressions (e.g. a stray ``import`` that breaks) are caught
by CI and so that code coverage reflects the actual shipped source tree.
"""

from __future__ import annotations

import importlib
import unittest


PLACEHOLDER_MODULES = [
    "app",
    "app.api",
    "app.api.v1",
    "app.core",
    "app.core.exceptions",
    "app.core.logging",
    "app.core.middleware",
    "app.core.security",
    "app.db",
    "app.db.base",
    "app.db.session",
    "app.domains",
    "app.policies",
    "app.repositories",
]


class PlaceholderModuleImportTests(unittest.TestCase):
    def test_all_placeholder_modules_import_cleanly(self) -> None:
        for name in PLACEHOLDER_MODULES:
            with self.subTest(module=name):
                module = importlib.import_module(name)
                self.assertIsNotNone(module)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    unittest.main()
