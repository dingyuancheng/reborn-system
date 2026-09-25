import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_admin
from app.models import Family, User
from app.schemas.family_schemas import FamilyCreate, FamilyOut, FamilyUpdate

router = APIRouter(prefix="/api/admin/families", tags=["admin-families"])


@router.get("", response_model=list[FamilyOut])
async def list_families(
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Family).where(Family.deleted == False).order_by(Family.create_time.desc())
    )
    families = list(result.scalars().all())
    return [FamilyOut.model_validate(f) for f in families]


@router.post("", response_model=FamilyOut, status_code=status.HTTP_201_CREATED)
async def create_family(
    payload: FamilyCreate,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    family = Family(name=payload.name, address=payload.address, description=payload.description)
    db.add(family)
    await db.commit()
    await db.refresh(family)
    return FamilyOut.model_validate(family)


@router.get("/{family_id}", response_model=FamilyOut)
async def get_family(
    family_id: uuid.UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Family).where(Family.id == family_id, Family.deleted == False))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="家庭不存在")
    return FamilyOut.model_validate(family)


@router.put("/{family_id}", response_model=FamilyOut)
async def update_family(
    family_id: uuid.UUID,
    payload: FamilyUpdate,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Family).where(Family.id == family_id, Family.deleted == False))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="家庭不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(family, field, value)
    await db.commit()
    await db.refresh(family)
    return FamilyOut.model_validate(family)


@router.delete("/{family_id}")
async def delete_family(
    family_id: uuid.UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Family).where(Family.id == family_id, Family.deleted == False))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="家庭不存在")

    member_count_stmt = select(User).where(User.family_id == family_id, User.deleted == False)
    member_count_result = await db.execute(member_count_stmt)
    member_count = len(list(member_count_result.scalars().all()))
    if member_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该家庭还有 {member_count} 名成员，无法删除。请先移除所有成员",
        )

    family.deleted = True
    await db.commit()
    return {"message": "家庭已删除"}