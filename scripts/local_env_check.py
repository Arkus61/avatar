import os
import socket
import sys
import urllib.error
import urllib.request
import subprocess


def check_http(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        response = urllib.request.urlopen(url, timeout=timeout)
        return response.status == 200, f"{url} -> {response.status}"
    except urllib.error.URLError as exc:
        return False, f"{url} -> error: {exc}"


def check_tcp(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True, f"tcp://{host}:{port} -> open"
    except OSError as exc:
        return False, f"tcp://{host}:{port} -> error: {exc}"
    finally:
        sock.close()


def check_postgres_service(host: str, port: int) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "avatar-postgres",
                "pg_isready",
                "-h",
                host,
                "-p",
                str(port),
                "-U",
                os.getenv("DB_USER", "avatar"),
                "-d",
                os.getenv("DB_NAME", "avatar"),
            ],
            capture_output=True,
            text=True,
            timeout=6,
        )
    except Exception as exc:
        return False, f"docker exec pg_isready error: {exc}"

    if result.returncode == 0:
        return True, result.stdout.strip() or "pg_isready ok"
    return False, (result.stderr or result.stdout).strip() or "pg_isready failed"


def check_local_postgres_psql() -> tuple[bool, str]:
    command = os.getenv("LOCAL_PG_CHECK_CMD")
    if command:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=8,
            )
        except Exception as exc:
            return False, f"local pg check error: {exc}"

        if result.returncode == 0:
            return True, (result.stdout or "local postgres check ok").strip()
        return False, (result.stderr or result.stdout or "local postgres check failed").strip()

    return True, "skipped (set LOCAL_PG_CHECK_CMD to enable command check)"


def main() -> int:
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "5432"))
    web_health_url = os.getenv("WEB_HEALTH_URL", "http://127.0.0.1:3010/health")
    api_health_url = os.getenv("API_HEALTH_URL", "http://127.0.0.1:8000/api/v1/health")

    checks = [
        ("web_health", *check_http(web_health_url)),
        ("api_health", *check_http(api_health_url)),
        ("db_tcp", *check_tcp(db_host, db_port)),
    ]

    use_local_postgres = os.getenv("DB_MODE", "docker").lower() == "local"
    if use_local_postgres:
        checks.append(("db_local_check", *check_local_postgres_psql()))
    else:
        checks.append(("db_pg_isready", *check_postgres_service(db_host, db_port)))

    has_failures = False
    for check_name, ok, details in checks:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {check_name}: {details}")
        if not ok:
            has_failures = True

    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
