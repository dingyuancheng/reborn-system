import json
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.deps import require_admin
from app.redis_client import get_redis

router = APIRouter(prefix="/api/admin/redis", tags=["admin-redis"])


@router.get("/keys")
async def list_keys(
    pattern: str = Query(default="reborn-*", description="Redis key 匹配模式"),
    current_user: dict[str, Any] = Depends(require_admin),
):
    redis = get_redis()
    keys = await redis.keys(pattern)
    result: list[dict[str, Any]] = []
    for key in sorted(keys):
        key_type = await redis.type(key)
        ttl = await redis.ttl(key)
        value: Any = None
        if key_type == "string":
            raw = await redis.get(key)
            try:
                value = json.loads(raw) if raw else None
            except (json.JSONDecodeError, TypeError):
                value = raw
        result.append({
            "key": key,
            "type": key_type,
            "ttl": ttl,
            "value": value,
        })
    return {"pattern": pattern, "count": len(result), "keys": result}


@router.get("/info")
async def redis_info(current_user: dict[str, Any] = Depends(require_admin)):
    redis = get_redis()
    info = await redis.info("server")
    dbsize = await redis.dbsize()
    return {
        "redis_version": info.get("redis_version"),
        "used_memory_human": info.get("used_memory_human"),
        "connected_clients": info.get("connected_clients"),
        "uptime_in_days": info.get("uptime_in_days"),
        "dbsize": dbsize,
    }