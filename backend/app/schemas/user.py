from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


from pydantic import BaseModel, EmailStr, Field

class UserCreate(UserBase):
    password: str = Field(min_length=8)
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int
    created_at: Optional[datetime] = None
    is_superuser: bool = False

    model_config = {"from_attributes": True}
