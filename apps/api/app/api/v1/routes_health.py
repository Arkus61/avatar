from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.health import check_db_tcp

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    db_ok, db_target = check_db_tcp()
    return {
        "data": {"status": "ok"},
        "meta": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "trace_id": getattr(request.state, "trace_id", "unknown"),
            "db_tcp": {"ok": db_ok, "target": db_target},
        },
    }
