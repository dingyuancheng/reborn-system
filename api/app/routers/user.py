from typing import Any, List, Optional

import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Menu, MenuCategory, UserActionLog, UserMenu, UserMenuClick
from app.schemas.menu_schemas import (
    MenuCategoryOut, MenuSimpleOut, MyMenusResponse,
)

router = APIRouter(prefix="/api/user", tags=["user"])


def _extract_device_info(user_agent: str) -> str:
    ua_lower = user_agent.lower() if user_agent else ""
    if "android" in ua_lower:
        return "Android App"
    if "iphone" in ua_lower or "ipad" in ua_lower:
        return "iOS App"
    if "capacitor" in ua_lower:
        return "Capacitor WebView"
    if "postman" in ua_lower:
        return "Postman"
    if "curl" in ua_lower:
        return "curl"
    if "chrome" in ua_lower:
        return "Chrome Browser"
    if "firefox" in ua_lower:
        return "Firefox Browser"
    if "safari" in ua_lower:
        return "Safari Browser"
    if "edg/" in ua_lower:
        return "Edge Browser"
    return "Web Browser"


def _extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return ""


class MenuClickRequest(BaseModel):
    menu_id: uuid.UUID


@router.get("/my-menus", response_model=MyMenusResponse)
async def my_menus(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id_str = current_user["userId"]
    user_id = uuid.UUID(user_id_str)
    now = datetime.utcnow()

    menu_ids_stmt = select(UserMenu.menu_id).where(UserMenu.user_id == user_id)
    menu_ids_result = await db.execute(menu_ids_stmt)
    granted_menu_ids = [row[0] for row in menu_ids_result.all()]

    if not granted_menu_ids:
        return MyMenusResponse(categories=[], menus=[], frequent_menus=[])

    valid_menus_stmt = select(Menu).where(
        Menu.id.in_(granted_menu_ids),
        Menu.deleted == False,
        Menu.status == 1,
        Menu.visible == 1,
        or_(Menu.start_time == None, Menu.start_time <= now),
        or_(Menu.end_time == None, Menu.end_time >= now),
    ).order_by(Menu.sort.asc())
    valid_menus_result = await db.execute(valid_menus_stmt)
    valid_menus = list(valid_menus_result.scalars().all())

    if not valid_menus:
        return MyMenusResponse(categories=[], menus=[], frequent_menus=[])

    category_ids = list({m.category_id for m in valid_menus})
    categories_stmt = select(MenuCategory).where(
        MenuCategory.id.in_(category_ids),
        MenuCategory.deleted == False,
        MenuCategory.status == 1,
    ).order_by(MenuCategory.sort.asc())
    categories_result = await db.execute(categories_stmt)
    categories = list(categories_result.scalars().all())

    frequent_stmt = (
        select(UserMenuClick, Menu)
        .join(Menu, Menu.id == UserMenuClick.menu_id)
        .where(
            UserMenuClick.user_id == user_id,
            Menu.id.in_([m.id for m in valid_menus]),
            Menu.deleted == False,
        )
        .order_by(UserMenuClick.click_count.desc(), UserMenuClick.last_click.desc())
        .limit(6)
    )
    frequent_result = await db.execute(frequent_stmt)
    frequent_menus = [row[1] for row in frequent_result.all()]

    return MyMenusResponse(
        categories=[MenuCategoryOut.model_validate(c) for c in categories],
        menus=[MenuSimpleOut.model_validate(m) for m in valid_menus],
        frequent_menus=[MenuSimpleOut.model_validate(m) for m in frequent_menus],
    )


@router.post("/menu-click")
async def menu_click(
    payload: MenuClickRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(current_user["userId"])
    menu_id = payload.menu_id
    now = datetime.utcnow()

    perm_check = await db.execute(
        select(UserMenu).where(UserMenu.user_id == user_id, UserMenu.menu_id == menu_id)
    )
    if not perm_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="无权限访问该菜单")

    menu_check = await db.execute(select(Menu).where(Menu.id == menu_id))
    menu = menu_check.scalar_one_or_none()
    if not menu or menu.deleted or menu.status != 1 or menu.visible != 1:
        raise HTTPException(status_code=403, detail="菜单已不可用")
    if menu.start_time and menu.start_time > now:
        raise HTTPException(status_code=403, detail="菜单尚未开放")
    if menu.end_time and menu.end_time < now:
        raise HTTPException(status_code=403, detail="菜单已过期")

    exists_stmt = select(UserMenuClick).where(
        UserMenuClick.user_id == user_id,
        UserMenuClick.menu_id == menu_id,
    )
    exists_result = await db.execute(exists_stmt)
    existing = exists_result.scalar_one_or_none()

    if existing:
        existing.click_count += 1
        existing.last_click = datetime.utcnow()
    else:
        new_record = UserMenuClick(
            user_id=user_id,
            menu_id=menu_id,
            click_count=1,
            last_click=datetime.utcnow(),
        )
        db.add(new_record)

    ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    device_info = _extract_device_info(user_agent)
    action_log = UserActionLog(
        user_id=user_id,
        username=current_user.get("username", ""),
        menu_id=menu_id,
        menu_name=menu.name,
        url=menu.url,
        action_type="click",
        ip=ip,
        user_agent=user_agent[:1000] if user_agent else None,
        device_info=device_info,
    )
    db.add(action_log)

    await db.commit()
    return {"message": "ok"}