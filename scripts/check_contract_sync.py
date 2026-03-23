import json
import re
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "packages" / "contracts" / "version.txt"
OPENAPI_FILE = ROOT / "packages" / "contracts" / "openapi" / "openapi.json"
CLIENT_FILE = ROOT / "packages" / "contracts" / "generated" / "client.ts"


def fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def main() -> int:
    if not VERSION_FILE.exists():
        return fail(f"Missing version file: {VERSION_FILE}")
    if not OPENAPI_FILE.exists():
        return fail(f"Missing OpenAPI file: {OPENAPI_FILE}")
    if not CLIENT_FILE.exists():
        return fail(f"Missing generated client file: {CLIENT_FILE}")

    version = VERSION_FILE.read_text(encoding="utf-8").strip()

    openapi = json.loads(OPENAPI_FILE.read_text(encoding="utf-8"))
    openapi_version = openapi.get("info", {}).get("version")
    if openapi_version != version:
        return fail(
            f"OpenAPI version mismatch: info.version={openapi_version!r}, expected={version!r}"
        )

    if "/api/v1/health" not in openapi.get("paths", {}):
        return fail("OpenAPI missing required path '/api/v1/health'")

    client_content = CLIENT_FILE.read_text(encoding="utf-8")
    match = re.search(r'CONTRACT_VERSION\s*=\s*"([^"]+)"', client_content)
    if not match:
        return fail("Generated client missing CONTRACT_VERSION marker")

    client_version = match.group(1)
    if client_version != version:
        return fail(
            f"Client version mismatch: CONTRACT_VERSION={client_version!r}, expected={version!r}"
        )

    # Validate static contract against runtime OpenAPI from backend app.
    api_app_dir = ROOT / "apps" / "api"
    sys.path.insert(0, str(api_app_dir))
    try:
        from app.main import app  # type: ignore
    except Exception as exc:
        return fail(f"Unable to import backend app for runtime OpenAPI check: {exc}")

    try:
        runtime_openapi = app.openapi()
    except Exception as exc:
        return fail(f"Unable to generate runtime OpenAPI schema: {exc}")

    runtime_version = runtime_openapi.get("info", {}).get("version")
    if runtime_version != version:
        return fail(
            f"Runtime OpenAPI version mismatch: runtime={runtime_version!r}, expected={version!r}"
        )

    runtime_paths = runtime_openapi.get("paths", {})
    if "/api/v1/health" not in runtime_paths:
        return fail("Runtime OpenAPI missing required path '/api/v1/health'")

    print("[OK] Contracts are in sync with static and runtime OpenAPI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
