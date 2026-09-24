import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_admin
from app.models import Menu, MenuCategory
from app.schemas.menu_schemas import (
    MenuCategoryCreate, MenuCategoryOut, MenuCategoryUpdate,
)

router = APIRouter(prefix="/api/admin/categories", tags=["admin-categories"])


@router.get("", response_model=list[MenuCategoryOut])
async def list_categories(
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MenuCategory).where(MenuCategory.deleted == False).order_by(MenuCategory.sort.asc())
    )
    categories = list(result.scalars().all())

    if categories:
        cat_ids = [c.id for c in categories]
        count_result = await db.execute(
            select(Menu.category_id, func.count(Menu.id))
            .where(Menu.category_id.in_(cat_ids), Menu.deleted == False)
            .group_by(Menu.category_id)
        )
        count_map = {row[0]: row[1] for row in count_result.all()}
    else:
        count_map = {}

    return [
        MenuCategoryOut(
            id=c.id,
            name=c.name,
            icon=c.icon,
            sort=c.sort,
            status=c.status,
            menu_count=count_map.get(c.id, 0),
        )
        for c in categories
    ]


@router.post("", response_model=MenuCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: MenuCategoryCreate,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    category = MenuCategory(
        name=payload.name,
        icon=payload.icon,
        sort=payload.sort,
        status=payload.status,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return MenuCategoryOut.model_validate(category)


@router.get("/{category_id}", response_model=MenuCategoryOut)
async def get_category(
    category_id: uuid.UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MenuCategory).where(MenuCategory.id == category_id, MenuCategory.deleted == False)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return MenuCategoryOut.model_validate(category)


@router.put("/{category_id}", response_model=MenuCategoryOut)
async def update_category(
    category_id: uuid.UUID,
    payload: MenuCategoryUpdate,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MenuCategory).where(MenuCategory.id == category_id, MenuCategory.deleted == False)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return MenuCategoryOut.model_validate(category)


@router.delete("/{category_id}")
async def delete_category(
    category_id: uuid.UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MenuCategory).where(MenuCategory.id == category_id, MenuCategory.deleted == False)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    menu_count_result = await db.execute(
        select(func.count(Menu.id)).where(Menu.category_id == category_id, Menu.deleted == False)
    )
    menu_count = menu_count_result.scalar()
    if menu_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该分类下还有 {menu_count} 个菜单，无法删除",
        )

    category.deleted = True
    await db.commit()
    return {"message": "分类已删除"}