import uuid
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_admin
from app.models import Family, User
from app.redis_client import kick_user_sessions
from app.schemas.user_schemas import UserCreate, UserOut, UserSimpleOut, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


class ResetPasswordRequest(BaseModel):
    new_password: str


class BanUserRequest(BaseModel):
    ban_flag: bool = True
    ban_time: Optional[str] = None
    ban_reason: Optional[str] = None


@router.get("", response_model=list[UserSimpleOut])
async def list_users(
    family_id: Optional[uuid.UUID] = None,
    deleted: Optional[bool] = None,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)
    if deleted is not None:
        stmt = stmt.where(User.deleted == deleted)
    if family_id:
        stmt = stmt.where(User.family_id == family_id)
    stmt = stmt.order_by(User.create_time.desc())
    result = await db.execute(stmt)
    users = list(result.scalars().all())
    return [UserSimpleOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.username == payload.username, User.deleted == False))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    family = None
    if payload.family_id:
        family_stmt = select(Family).where(Family.id == payload.family_id, Family.deleted == False)
        family_result = await db.execute(family_stmt)
        family = family_result.scalar_one_or_none()
        if not family:
            raise HTTPException(status_code=400, detail="指定的家庭不存在")

    user = User(
        username=payload.username,
        nickname=payload.nickname,
        phone=payload.phone,
        email=payload.email,
        password=hash_password(payload.password),
        avatar=payload.avatar,
        gender=payload.gender,
        birthday=payload.birthday,
        family_id=payload.family_id,
        admin_flag=payload.admin_flag,
        status=payload.status,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    if family:
        family.member_count += 1
        await db.commit()

    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: uuid.UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id, User.deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id, User.deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        old_status = user.status
        old_family_id = user.family_id
        for field, value in update_data.items():
            setattr(user, field, value)

        if "family_id" in update_data:
            if old_family_id:
                old_fam_result = await db.execute(select(Family).where(Family.id == old_family_id))
                old_fam = old_fam_result.scalar_one_or_none()
                if old_fam and old_fam.member_count > 0:
                    old_fam.member_count -= 1
            if user.family_id:
                new_fam_result = await db.execute(select(Family).where(Family.id == user.family_id))
                new_fam = new_fam_result.scalar_one_or_none()
                if new_fam:
                    new_fam.member_count += 1

        await db.commit()
        await db.refresh(user)

        if old_status == 1 and user.status == 0:
            await kick_user_sessions(
                user_id=str(user.id),
                reason="账号已被禁用，请联系管理员",
            )

    return UserOut.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id, User.deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if str(user.id) == current_user.get("userId"):
        raise HTTPException(status_code=400, detail="不能删除自己")

    old_family_id = user.family_id
    user.deleted = True
    await db.commit()

    await kick_user_sessions(
        user_id=str(user.id),
        reason="账号已失效，请重新注册或联系管理员",
    )

    if old_family_id:
        fam_result = await db.execute(select(Family).where(Family.id == old_family_id))
        fam = fam_result.scalar_one_or_none()
        if fam and fam.member_count > 0:
            fam.member_count -= 1
            await db.commit()

    return {"message": "用户已删除"}


@router.post("/{user_id}/restore")
async def restore_user(
    user_id: uuid.UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not user.deleted:
        raise HTTPException(status_code=400, detail="该用户未失效")

    user.deleted = False
    await db.commit()

    if user.family_id:
        fam_result = await db.execute(select(Family).where(Family.id == user.family_id))
        fam = fam_result.scalar_one_or_none()
        if fam:
            fam.member_count += 1
            await db.commit()

    return {"message": "用户已恢复"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: uuid.UUID,
    payload: ResetPasswordRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id, User.deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password = hash_password(payload.new_password)
    await db.commit()

    kicked = await kick_user_sessions(
        user_id=str(user.id),
        reason="密码已修改，请重新登录",
    )

    return {"message": "密码已重置", "kicked_sessions": kicked}


@router.put("/{user_id}/ban")
async def ban_user(
    user_id: uuid.UUID,
    payload: BanUserRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id, User.deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if str(user.id) == current_user.get("userId"):
        raise HTTPException(status_code=400, detail="不能封禁自己")

    user.ban_flag = payload.ban_flag
    user.ban_time = payload.ban_time or None
    user.ban_reason = payload.ban_reason or None if payload.ban_flag else None
    if not payload.ban_flag:
        user.ban_time = None
        user.ban_reason = None
    await db.commit()
    await db.refresh(user)

    kicked = 0
    if payload.ban_flag:
        kicked = await kick_user_sessions(
            user_id=str(user.id),
            reason=f"账号已被封禁，原因：{payload.ban_reason or '未说明'}",
        )

    return {"message": "封禁状态已更新", "ban_flag": user.ban_flag, "kicked_sessions": kicked}