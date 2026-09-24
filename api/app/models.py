import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "t_user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gender: Mapped[int] = mapped_column(SmallInteger, default=0)
    birthday: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    family_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_family.id", ondelete="SET NULL"), nullable=True
    )
    admin_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    ban_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ban_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_login_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    family: Mapped[Optional["Family"]] = relationship("Family", back_populates="users")


class Family(Base):
    __tablename__ = "t_family"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="family")


class MenuCategory(Base):
    __tablename__ = "t_menu_category"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    menus: Mapped[list["Menu"]] = relationship("Menu", back_populates="category")


class Menu(Base):
    __tablename__ = "t_menu"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_menu_category.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    visible: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    category: Mapped["MenuCategory"] = relationship("MenuCategory", back_populates="menus")
    user_permissions: Mapped[list["UserMenu"]] = relationship("UserMenu", back_populates="menu", cascade="all, delete-orphan")
    click_records: Mapped[list["UserMenuClick"]] = relationship("UserMenuClick", back_populates="menu", cascade="all, delete-orphan")


class UserMenu(Base):
    __tablename__ = "t_user_menu"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False
    )
    menu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_menu.id", ondelete="CASCADE"), nullable=False
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
    menu: Mapped["Menu"] = relationship("Menu", back_populates="user_permissions")


class UserMenuClick(Base):
    __tablename__ = "t_user_menu_click"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False
    )
    menu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_menu.id", ondelete="CASCADE"), nullable=False
    )
    click_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_click: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
    menu: Mapped["Menu"] = relationship("Menu", back_populates="click_records")


class UserLoginLog(Base):
    __tablename__ = "t_user_login_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_user.id", ondelete="SET NULL"), nullable=True
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    login_result: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    fail_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    login_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserActionLog(Base):
    __tablename__ = "t_user_action_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    menu_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_menu.id", ondelete="SET NULL"), nullable=True
    )
    menu_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action_type: Mapped[str] = mapped_column(String(32), default="click", nullable=False)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )