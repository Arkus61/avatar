from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    api_app_dir = root / "apps" / "api"
    sys.path.insert(0, str(api_app_dir))

    try:
        from app.main import app  # type: ignore
    except Exception as exc:  # pragma: no cover - CI runtime guard
        print(f"[FAIL] Unable to import FastAPI app: {exc}")
        return 1

    try:
        openapi = app.openapi()
    except Exception as exc:  # pragma: no cover - CI runtime guard
        print(f"[FAIL] Unable to generate OpenAPI schema: {exc}")
        return 1

    if openapi.get("info", {}).get("version") != "0.1.0":
        print("[FAIL] Unexpected API version in OpenAPI schema")
        return 1

    if "/api/v1/health" not in openapi.get("paths", {}):
        print("[FAIL] OpenAPI schema missing '/api/v1/health'")
        return 1

    print("[OK] API build check passed (import + OpenAPI generation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
