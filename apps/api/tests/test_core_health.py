"""Tests for app.core.health — check_db_tcp()."""
import sys
import os
import socket
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))

from app.core.health import check_db_tcp


class TestCheckDbTcp(unittest.TestCase):
    def _mock_socket(self, connect_side_effect=None):
        mock_sock = MagicMock()
        if connect_side_effect is not None:
            mock_sock.connect.side_effect = connect_side_effect
        return mock_sock

    def test_returns_true_on_successful_connection(self) -> None:
        mock_sock = self._mock_socket()
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            ok, target = check_db_tcp()
        self.assertTrue(ok)
        self.assertEqual(target, "127.0.0.1:5432")

    def test_returns_false_on_os_error(self) -> None:
        mock_sock = self._mock_socket(connect_side_effect=OSError("refused"))
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            ok, target = check_db_tcp()
        self.assertFalse(ok)
        self.assertEqual(target, "127.0.0.1:5432")

    def test_socket_always_closed_on_success(self) -> None:
        mock_sock = self._mock_socket()
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            check_db_tcp()
        mock_sock.close.assert_called_once()

    def test_socket_always_closed_on_failure(self) -> None:
        mock_sock = self._mock_socket(connect_side_effect=OSError("timeout"))
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            check_db_tcp()
        mock_sock.close.assert_called_once()

    def test_timeout_set_to_two_seconds(self) -> None:
        mock_sock = self._mock_socket()
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            check_db_tcp()
        mock_sock.settimeout.assert_called_once_with(2.0)

    def test_uses_env_db_host(self) -> None:
        mock_sock = self._mock_socket()
        os.environ["DB_HOST"] = "db.internal"
        try:
            with patch("app.core.health.socket.socket", return_value=mock_sock):
                ok, target = check_db_tcp()
            self.assertIn("db.internal", target)
        finally:
            del os.environ["DB_HOST"]

    def test_uses_env_db_port(self) -> None:
        mock_sock = self._mock_socket()
        os.environ["DB_PORT"] = "9999"
        try:
            with patch("app.core.health.socket.socket", return_value=mock_sock):
                ok, target = check_db_tcp()
            self.assertIn("9999", target)
        finally:
            del os.environ["DB_PORT"]

    def test_uses_env_db_host_and_port_together(self) -> None:
        mock_sock = self._mock_socket()
        os.environ["DB_HOST"] = "pg-host"
        os.environ["DB_PORT"] = "5433"
        try:
            with patch("app.core.health.socket.socket", return_value=mock_sock):
                ok, target = check_db_tcp()
            self.assertEqual(target, "pg-host:5433")
            mock_sock.connect.assert_called_once_with(("pg-host", 5433))
        finally:
            del os.environ["DB_HOST"]
            del os.environ["DB_PORT"]

    def test_connect_called_with_correct_args_defaults(self) -> None:
        for var in ("DB_HOST", "DB_PORT"):
            os.environ.pop(var, None)
        mock_sock = self._mock_socket()
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            check_db_tcp()
        mock_sock.connect.assert_called_once_with(("127.0.0.1", 5432))

    def test_socket_created_with_correct_family_and_type(self) -> None:
        mock_sock = self._mock_socket()
        with patch("app.core.health.socket.socket", return_value=mock_sock) as mock_ctor:
            check_db_tcp()
        mock_ctor.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)

    def test_return_type_is_tuple(self) -> None:
        mock_sock = self._mock_socket()
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            result = check_db_tcp()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)

    def test_connection_refused_returns_correct_target_string(self) -> None:
        mock_sock = self._mock_socket(connect_side_effect=ConnectionRefusedError())
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            ok, target = check_db_tcp()
        self.assertFalse(ok)
        self.assertIn(":", target)

    def test_timeout_error_treated_as_os_error(self) -> None:
        mock_sock = self._mock_socket(connect_side_effect=TimeoutError())
        with patch("app.core.health.socket.socket", return_value=mock_sock):
            ok, target = check_db_tcp()
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
