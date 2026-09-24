import json
import time
import uuid
from typing import Any, Optional

import redis.asyncio as redis

from app.config import (
    KICK_REASON_KEY_PREFIX,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    REDIS_SESSION_TTL,
)

KEY_PREFIX = "reborn-session-"

_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            decode_responses=True,
        )
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


async def create_session(user_data: dict[str, Any], ttl: int = REDIS_SESSION_TTL) -> str:
    session_id = uuid.uuid4().hex
    key = f"{KEY_PREFIX}{session_id}"
    payload = json.dumps(user_data, default=str, ensure_ascii=False)
    await get_redis().setex(key, ttl, payload)
    return session_id


async def get_session(session_id: str) -> Optional[dict[str, Any]]:
    key = f"{KEY_PREFIX}{session_id}"
    data = await get_redis().get(key)
    if data is None:
        return None
    return json.loads(data)


async def touch_session(session_id: str) -> None:
    key = f"{KEY_PREFIX}{session_id}"
    data = await get_redis().get(key)
    if data is None:
        return
    payload = json.loads(data)
    payload["lastActiveTime"] = time.strftime("%Y-%m-%d %H:%M:%S")
    await get_redis().setex(key, REDIS_SESSION_TTL, json.dumps(payload, ensure_ascii=False))


async def delete_session(session_id: str) -> None:
    key = f"{KEY_PREFIX}{session_id}"
    await get_redis().delete(key)


async def mark_kicked(session_id: str, reason: str = "账号已在其他设备登录") -> None:
    key = f"{KICK_REASON_KEY_PREFIX}{session_id}"
    payload = json.dumps({"reason": reason, "kick_time": time.strftime("%Y-%m-%d %H:%M:%S")})
    await get_redis().setex(key, REDIS_SESSION_TTL, payload)


async def get_kick_info(session_id: str) -> Optional[dict]:
    key = f"{KICK_REASON_KEY_PREFIX}{session_id}"
    data = await get_redis().get(key)
    if data is None:
        return None
    return json.loads(data)


async def clear_kick_info(session_id: str) -> None:
    key = f"{KICK_REASON_KEY_PREFIX}{session_id}"
    await get_redis().delete(key)


async def kick_user_sessions(
    user_id: str,
    exclude_session_id: str | None = None,
    device_type: str | None = None,
    reason: str = "账号已在其他设备登录",
) -> int:
    """踢掉某个用户的在线 session（排除 exclude_session_id）。

    若指定 device_type，则只踢相同设备类型的 session（手机踢手机、电脑踢电脑），
    不同设备类型的 session 保留共存。未指定 device_type 时踢掉该用户所有 session。
    遍历所有 session key，找到 userId 匹配的，删除 session 并写入 kick 通知。
    返回被踢掉的 session 数量。
    """
    redis_client = get_redis()
    kicked = 0
    async for key in redis_client.scan_iter(match=f"{KEY_PREFIX}*"):
        data = await redis_client.get(key)
        if not data:
            continue
        try:
            payload = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            continue
        if payload.get("userId") != str(user_id):
            continue
        old_session_id = key[len(KEY_PREFIX):]
        if exclude_session_id and old_session_id == exclude_session_id:
            continue
        if device_type:
            old_device_type = payload.get("deviceType") or "desktop"
            if old_device_type != device_type:
                continue
        await redis_client.delete(key)
        await mark_kicked(old_session_id, reason)
        kicked += 1
    return kicked