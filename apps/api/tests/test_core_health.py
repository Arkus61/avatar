import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))

from app.core.health import check_db_tcp


class CheckDbTcpTests(unittest.TestCase):
    def test_check_db_tcp_returns_true_when_socket_connects(self) -> None:
        socket_instance = MagicMock()

        with (
            patch.dict(os.environ, {"DB_HOST": "db.internal", "DB_PORT": "15432"}, clear=False),
            patch("app.core.health.socket.socket", return_value=socket_instance) as socket_factory,
        ):
            ok, target = check_db_tcp()

        self.assertTrue(ok)
        self.assertEqual(target, "db.internal:15432")
        socket_factory.assert_called_once_with(socket_factory.call_args.args[0], socket_factory.call_args.args[1])
        self.assertEqual(socket_factory.call_args.args, (2, 1))
        socket_instance.settimeout.assert_called_once_with(2.0)
        socket_instance.connect.assert_called_once_with(("db.internal", 15432))
        socket_instance.close.assert_called_once_with()

    def test_check_db_tcp_returns_false_when_socket_raises_os_error(self) -> None:
        socket_instance = MagicMock()
        socket_instance.connect.side_effect = OSError("connection refused")

        with (
            patch.dict(os.environ, {}, clear=False),
            patch("app.core.health.socket.socket", return_value=socket_instance),
        ):
            os.environ.pop("DB_HOST", None)
            os.environ.pop("DB_PORT", None)
            ok, target = check_db_tcp()

        self.assertFalse(ok)
        self.assertEqual(target, "127.0.0.1:5432")
        socket_instance.settimeout.assert_called_once_with(2.0)
        socket_instance.connect.assert_called_once_with(("127.0.0.1", 5432))
        socket_instance.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
