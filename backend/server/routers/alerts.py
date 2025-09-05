from fastapi import APIRouter, HTTPException, Path, Query, Header
from ...common.db import get_session
from ..repositories.alerts_repo import (
    list_recent_alerts,
    list_recent_alerts_by_owner,
    get_alert,
    acknowledge_alert,
)

router = APIRouter()

@router.get("/recent", summary="Recent Alerts")
def recent_alerts(limit: int = Query(50, ge=1, le=500), x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    
    from ..services.auth_service import get_user_id_by_api_key
    uid = get_user_id_by_api_key(x_api_key)
    if uid is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    with get_session() as s:
        items = list_recent_alerts_by_owner(s, owner_id=uid, limit=limit)
        return {"items": items, "count": len(items)}

@router.get("/{alert_id}", summary="Get Alert by ID")
def get_alert_by_id(alert_id: int = Path(..., ge=1)):
    with get_session() as s:
        row = get_alert(s, alert_id)
        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")
        return row

@router.patch("/{alert_id}/ack", summary="Acknowledge Alert")
def ack_alert(alert_id: int = Path(..., ge=1)):
    with get_session() as s:
        ok = acknowledge_alert(s, alert_id, acknowledged=True)
        if not ok:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"ok": True, "id": alert_id, "acknowledged": True}
