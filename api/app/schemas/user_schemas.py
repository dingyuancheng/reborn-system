import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: int = 0
    birthday: Optional[datetime] = None
    family_id: Optional[uuid.UUID] = None
    admin_flag: bool = False
    status: int = 1
    ban_flag: bool = False
    ban_time: Optional[datetime] = None
    ban_reason: Optional[str] = None
    last_login_ip: Optional[str] = None
    last_login_time: Optional[datetime] = None
    create_time: datetime
    update_time: Optional[datetime] = None


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    nickname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    gender: int = 0
    birthday: Optional[datetime] = None
    family_id: Optional[uuid.UUID] = None
    admin_flag: bool = False
    status: int = 1


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[int] = None
    birthday: Optional[datetime] = None
    family_id: Optional[uuid.UUID] = None
    admin_flag: Optional[bool] = None
    status: Optional[int] = None
    ban_flag: Optional[bool] = None
    ban_time: Optional[datetime] = None
    ban_reason: Optional[str] = None


class UserSimpleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: int = 0
    family_id: Optional[uuid.UUID] = None
    admin_flag: bool = False
    status: int = 1
    ban_flag: bool = False
    deleted: bool = False
    last_login_time: Optional[datetime] = None