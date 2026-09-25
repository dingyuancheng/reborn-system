import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FamilyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    member_count: int = 0
    create_time: datetime
    update_time: Optional[datetime] = None


class FamilyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    address: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None


class FamilyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    address: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None