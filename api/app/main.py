from contextlib import asynccontextmanager
from pathlib import Path

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import STATIC_URL, UPLOAD_DIR
from app.database import Base, engine, AsyncSessionLocal
from app.models import (
    Family, Menu, MenuCategory, User, UserLoginLog, UserMenu, UserMenuClick, UserActionLog,
)
from app.routers import auth, users
from app.routers.admin import sessions as admin_sessions
from app.routers.admin import users as admin_users
from app.routers.admin import families as admin_families
from app.routers.admin import categories as admin_categories
from app.routers.admin import menus as admin_menus
from app.routers.admin import permissions as admin_permissions
from app.routers.admin import stats as admin_stats
from app.routers.admin import upload as admin_upload
from app.routers.admin import redis as admin_redis
from app.routers import user as app_user

DEFAULT_MENUS = [
    {"name": "家务分工", "url": "/chore/divide", "icon": "🧹", "external": 0, "category": "家务", "sort": 1},
    {"name": "今日做饭", "url": "/chore/cook", "icon": "🍳", "external": 0, "category": "家务", "sort": 2},
    {"name": "垃圾清运", "url": "/chore/trash", "icon": "🗑️", "external": 0, "category": "家务", "sort": 3},
    {"name": "家庭记账", "url": "/finance/bill", "icon": "💰", "external": 0, "category": "财务", "sort": 1},
    {"name": "收支报表", "url": "/finance/report", "icon": "📊", "external": 0, "category": "财务", "sort": 2},
    {"name": "家庭相册", "url": "/family/album", "icon": "📷", "external": 0, "category": "生活", "sort": 1},
    {"name": "今日日程", "url": "/schedule/today", "icon": "📅", "external": 0, "category": "生活", "sort": 2},
    {"name": "健康打卡", "url": "/health/checkin", "icon": "❤️", "external": 0, "category": "健康", "sort": 1},
    {"name": "豆包", "url": "https://www.doubao.com", "icon": "🤖", "external": 1, "category": "工具", "sort": 1},
    {"name": "设置", "url": "/settings/app", "icon": "⚙️", "external": 0, "category": "工具", "sort": 2},
]

DEFAULT_CATEGORIES = [
    {"name": "家务", "icon": "🧹", "sort": 1},
    {"name": "财务", "icon": "💰", "sort": 2},
    {"name": "生活", "icon": "🏠", "sort": 3},
    {"name": "健康", "icon": "❤️", "sort": 4},
    {"name": "工具", "icon": "🔧", "sort": 5},
]


async def _seed_data(session: AsyncSession):
    from sqlalchemy import func

    cat_count_result = await session.execute(
        select(func.count(MenuCategory.id)).where(MenuCategory.deleted == False)
    )
    if cat_count_result.scalar() == 0:
        cat_map: dict[str, uuid.UUID] = {}
        for cat_data in DEFAULT_CATEGORIES:
            cat = MenuCategory(
                name=cat_data["name"],
                icon=cat_data["icon"],
                sort=cat_data["sort"],
                status=1,
            )
            session.add(cat)
            await session.flush()
            cat_map[cat_data["name"]] = cat.id

        for menu_data in DEFAULT_MENUS:
            menu = Menu(
                category_id=cat_map[menu_data["category"]],
                name=menu_data["name"],
                url=menu_data["url"],
                icon=menu_data["icon"],
                sort=menu_data["sort"],
                external=menu_data["external"],
                visible=1,
                status=1,
            )
            session.add(menu)

        await session.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await _seed_data(session)

    yield
    await engine.dispose()


app = FastAPI(title="Reborn System API", version="0.1.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(app_user.router)

app.include_router(admin_sessions.router)
app.include_router(admin_users.router)
app.include_router(admin_families.router)
app.include_router(admin_categories.router)
app.include_router(admin_menus.router)
app.include_router(admin_permissions.router)
app.include_router(admin_stats.router)
app.include_router(admin_upload.router)
app.include_router(admin_redis.router)

upload_path = Path(UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount(STATIC_URL, StaticFiles(directory=str(upload_path)), name="static")