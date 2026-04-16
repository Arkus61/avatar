"""Tests for ``app.core.health.check_db_tcp``.

The function opens a TCP socket against ``DB_HOST``/``DB_PORT`` with a
short timeout. We exercise three branches:

1. The socket connects successfully (``ok=True``).
2. The connection fails with ``OSError`` (``ok=False``).
3. Environment variables override the default host/port.

We additionally assert that the socket is always closed regardless of
outcome, which is the contract of the ``finally`` branch.
"""

from __future__ import annotations

import socket
import unittest
from unittest import mock

from app.core import health


class FakeSocket:
    """Minimal stand-in for ``socket.socket`` used in check_db_tcp tests."""

    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail
        self.timeout: float | None = None
        self.connected_to: tuple[str, int] | None = None
        self.closed = False

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def connect(self, address: tuple[str, int]) -> None:
        if self._fail:
            raise OSError("refused")
        self.connected_to = address

    def close(self) -> None:
        self.closed = True


class CheckDbTcpTests(unittest.TestCase):
    def test_returns_ok_true_when_connection_succeeds(self) -> None:
        fake = FakeSocket(fail=False)
        with mock.patch.object(health.socket, "socket", return_value=fake), \
             mock.patch.dict(health.os.environ, {"DB_HOST": "127.0.0.1", "DB_PORT": "5432"}, clear=False):
            ok, target = health.check_db_tcp()

        self.assertTrue(ok)
        self.assertEqual(target, "127.0.0.1:5432")
        self.assertEqual(fake.connected_to, ("127.0.0.1", 5432))
        self.assertEqual(fake.timeout, 2.0)
        self.assertTrue(fake.closed)

    def test_returns_ok_false_when_connection_refused(self) -> None:
        fake = FakeSocket(fail=True)
        with mock.patch.object(health.socket, "socket", return_value=fake), \
             mock.patch.dict(health.os.environ, {"DB_HOST": "127.0.0.1", "DB_PORT": "5432"}, clear=False):
            ok, target = health.check_db_tcp()

        self.assertFalse(ok)
        self.assertEqual(target, "127.0.0.1:5432")
        self.assertTrue(fake.closed)

    def test_env_vars_override_host_and_port(self) -> None:
        fake = FakeSocket(fail=False)
        env = {"DB_HOST": "db.example.internal", "DB_PORT": "15432"}
        with mock.patch.object(health.socket, "socket", return_value=fake), \
             mock.patch.dict(health.os.environ, env, clear=False):
            ok, target = health.check_db_tcp()

        self.assertTrue(ok)
        self.assertEqual(target, "db.example.internal:15432")
        self.assertEqual(fake.connected_to, ("db.example.internal", 15432))

    def test_defaults_used_when_env_vars_missing(self) -> None:
        fake = FakeSocket(fail=False)
        clean_env = {
            k: v for k, v in health.os.environ.items() if k not in {"DB_HOST", "DB_PORT"}
        }
        with mock.patch.object(health.socket, "socket", return_value=fake), \
             mock.patch.dict(health.os.environ, clean_env, clear=True):
            ok, target = health.check_db_tcp()

        self.assertTrue(ok)
        self.assertEqual(target, "127.0.0.1:5432")
        self.assertEqual(fake.connected_to, ("127.0.0.1", 5432))

    def test_socket_is_always_closed(self) -> None:
        fake = FakeSocket(fail=True)
        with mock.patch.object(health.socket, "socket", return_value=fake):
            health.check_db_tcp()
        self.assertTrue(fake.closed)

    def test_uses_af_inet_stream_socket(self) -> None:
        created: list[tuple[int, int]] = []

        def fake_factory(family: int, kind: int) -> FakeSocket:
            created.append((family, kind))
            return FakeSocket(fail=False)

        with mock.patch.object(health.socket, "socket", side_effect=fake_factory):
            health.check_db_tcp()

        self.assertEqual(created, [(socket.AF_INET, socket.SOCK_STREAM)])


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    unittest.main()
