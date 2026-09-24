import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.deps import require_admin
from app.redis_client import get_redis, mark_kicked

router = APIRouter(prefix="/api/admin/sessions", tags=["admin-sessions"])


class SessionOut(BaseModel):
    session_id: str
    user_id: str
    username: str
    nickname: str
    family_id: str | None = None
    admin_flag: bool = False
    ip: str = ""
    device: str = ""
    user_agent: str = ""
    login_time: str | None = None
    last_active: str | None = None


@router.get("", response_model=list[SessionOut])
async def list_sessions(current_user: dict[str, Any] = Depends(require_admin)):
    redis = get_redis()
    pattern = "reborn-session-*"
    keys = await redis.keys(pattern)
    sessions: list[SessionOut] = []
    for key in keys:
        sid = key.replace("reborn-session-", "")
        data = await redis.get(key)
        if data:
            payload = json.loads(data)
            sessions.append(
                SessionOut(
                    session_id=sid,
                    user_id=payload.get("userId", ""),
                    username=payload.get("username", ""),
                    nickname=payload.get("nickname", ""),
                    family_id=payload.get("familyId"),
                    admin_flag=payload.get("adminFlag", False),
                    ip=payload.get("ip", ""),
                    device=payload.get("device", ""),
                    user_agent=payload.get("userAgent", ""),
                    login_time=payload.get("loginTime"),
                    last_active=payload.get("lastActiveTime"),
                )
            )
    return sessions


@router.delete("/{session_id}")
async def kick_session(
    session_id: str,
    reason: str = "管理员强制下线",
    current_user: dict[str, Any] = Depends(require_admin),
):
    redis = get_redis()
    key = f"reborn-session-{session_id}"
    deleted = await redis.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    await mark_kicked(session_id, reason)
    return {"message": "已踢下线", "reason": reason}


@router.get("/{session_id}/raw")
async def get_session_raw(
    session_id: str,
    current_user: dict[str, Any] = Depends(require_admin),
):
    redis = get_redis()
    key = f"reborn-session-{session_id}"
    data = await redis.get(key)
    ttl = await redis.ttl(key)
    if data is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        payload = data
    return {
        "key": key,
        "session_id": session_id,
        "ttl": ttl,
        "payload": payload,
    }