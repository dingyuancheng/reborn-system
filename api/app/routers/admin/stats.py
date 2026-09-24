from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_admin
from app.models import (
    Family, Menu, User, UserActionLog, UserLoginLog, UserMenuClick,
)
from app.redis_client import get_redis

router = APIRouter(prefix="/api/admin/stats", tags=["admin-stats"])


@router.get("")
async def dashboard_stats(
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(
        select(func.count(User.id)).where(User.deleted == False)
    )).scalar() or 0

    total_families = (await db.execute(
        select(func.count(Family.id)).where(Family.deleted == False)
    )).scalar() or 0

    total_menus = (await db.execute(
        select(func.count(Menu.id)).where(Menu.deleted == False, Menu.status == 1)
    )).scalar() or 0

    redis = get_redis()
    keys = await redis.keys("reborn-session-*")
    online_users = len(keys)

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_clicks = (await db.execute(
        select(func.count(UserActionLog.id)).where(
            UserActionLog.action_time >= today_start,
        )
    )).scalar() or 0

    top_menus_stmt = (
        select(Menu.name, Menu.icon, func.coalesce(func.sum(UserMenuClick.click_count), 0).label("total_count"))
        .outerjoin(UserMenuClick, UserMenuClick.menu_id == Menu.id)
        .where(Menu.deleted == False)
        .group_by(Menu.id)
        .order_by(func.coalesce(func.sum(UserMenuClick.click_count), 0).desc())
        .limit(6)
    )
    top_menus_result = await db.execute(top_menus_stmt)
    top_menus = [
        {"name": row[0], "icon": row[1], "click_count": int(row[2] or 0)}
        for row in top_menus_result.all()
    ]

    recent_users_stmt = (
        select(User.username, User.nickname, User.last_login_time)
        .where(User.deleted == False, User.last_login_time.isnot(None))
        .order_by(User.last_login_time.desc())
        .limit(5)
    )
    recent_users_result = await db.execute(recent_users_stmt)
    recent_users = [
        {
            "username": row[0],
            "nickname": row[1],
            "last_login_time": row[2].strftime("%Y-%m-%d %H:%M") if row[2] else None,
        }
        for row in recent_users_result.all()
    ]

    today_logins = (await db.execute(
        select(func.count(UserLoginLog.id)).where(
            UserLoginLog.login_time >= today_start,
            UserLoginLog.login_result == 1,
        )
    )).scalar() or 0

    return {
        "total_users": total_users,
        "online_users": online_users,
        "total_families": total_families,
        "total_menus": total_menus,
        "today_clicks": today_clicks,
        "today_logins": today_logins,
        "top_menus": top_menus,
        "recent_users": recent_users,
    }