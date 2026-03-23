import os
import socket


def check_db_tcp() -> tuple[bool, str]:
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "5432"))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    try:
        sock.connect((host, port))
        return True, f"{host}:{port}"
    except OSError:
        return False, f"{host}:{port}"
    finally:
        sock.close()
