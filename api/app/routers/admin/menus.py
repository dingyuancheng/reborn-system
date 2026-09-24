import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_admin
from app.models import Menu, MenuCategory
from app.schemas.menu_schemas import MenuCreate, MenuOut, MenuUpdate

router = APIRouter(prefix="/api/admin/menus", tags=["admin-menus"])


@router.get("", response_model=list[MenuOut])
async def list_menus(
    category_id: Optional[uuid.UUID] = Query(default=None),
    status_filter: Optional[int] = Query(default=None),
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Menu).where(Menu.deleted == False)
    if category_id:
        stmt = stmt.where(Menu.category_id == category_id)
    if status_filter is not None:
        stmt = stmt.where(Menu.status == status_filter)
    stmt = stmt.order_by(Menu.category_id.asc(), Menu.sort.asc())
    result = await db.execute(stmt)
    menus = list(result.scalars().all())
    return [MenuOut.model_validate(m) for m in menus]


@router.post("", response_model=MenuOut, status_code=status.HTTP_201_CREATED)
async def create_menu(
    payload: MenuCreate,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cat_result = await db.execute(
        select(MenuCategory).where(MenuCategory.id == payload.category_id, MenuCategory.deleted == False)
    )
    if not cat_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="指定的分类不存在")

    menu = Menu(
        category_id=payload.category_id,
        name=payload.name,
        url=payload.url,
        icon=payload.icon,
        sort=payload.sort,
        external=payload.external,
        visible=payload.visible,
        status=payload.status,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return MenuOut.model_validate(menu)


@router.get("/{menu_id}", response_model=MenuOut)
async def get_menu(
    menu_id: uuid.UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Menu).where(Menu.id == menu_id, Menu.deleted == False))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    return MenuOut.model_validate(menu)


@router.put("/{menu_id}", response_model=MenuOut)
async def update_menu(
    menu_id: uuid.UUID,
    payload: MenuUpdate,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Menu).where(Menu.id == menu_id, Menu.deleted == False))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(menu, field, value)
    await db.commit()
    await db.refresh(menu)
    return MenuOut.model_validate(menu)


@router.put("/{menu_id}/status", response_model=MenuOut)
async def update_menu_status(
    menu_id: uuid.UUID,
    payload: dict,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Menu).where(Menu.id == menu_id, Menu.deleted == False))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    if "status" in payload:
        menu.status = payload["status"]
    if "visible" in payload:
        menu.visible = payload["visible"]
    await db.commit()
    await db.refresh(menu)
    return MenuOut.model_validate(menu)


@router.delete("/{menu_id}")
async def delete_menu(
    menu_id: uuid.UUID,
    hard: bool = Query(default=False),
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Menu).where(Menu.id == menu_id, Menu.deleted == False))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")

    if hard:
        await db.delete(menu)
        await db.commit()
        return {"message": "菜单已永久删除"}
    else:
        menu.deleted = True
        menu.status = 0
        await db.commit()
        return {"message": "菜单已删除"}