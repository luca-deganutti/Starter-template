from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255)
    is_active: bool = Field(..., default=True)



class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=255)
    role: Literal["admin", "user"] | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    id: int
    is_active: bool
    role: Literal["admin", "user"]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
