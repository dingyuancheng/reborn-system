import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MenuCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    sort: int = 0
    status: int = 1
    menu_count: int = 0


class MenuCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    sort: int = 0
    status: int = 1


class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=32)
    sort: Optional[int] = None
    status: Optional[int] = None


class MenuOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    url: str
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    sort: int = 0
    external: int = 0
    visible: int = 1
    status: int = 1
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class MenuCreate(BaseModel):
    category_id: uuid.UUID
    name: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=1, max_length=255)
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    sort: int = 0
    external: int = 0
    visible: int = 1
    status: int = 1
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class MenuUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    url: Optional[str] = Field(default=None, min_length=1, max_length=255)
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    sort: Optional[int] = None
    external: Optional[int] = None
    visible: Optional[int] = None
    status: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class MenuSimpleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    url: str
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    external: int = 0


class MyMenusResponse(BaseModel):
    categories: list[MenuCategoryOut]
    menus: list[MenuSimpleOut]
    frequent_menus: list[MenuSimpleOut]