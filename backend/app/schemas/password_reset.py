"""
API Schemas cho đặt lại mật khẩu.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class ForgotPasswordRequest(BaseModel):
    """Dữ liệu yêu cầu quên mật khẩu."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Dữ liệu yêu cầu đặt lại mật khẩu."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetResponse(BaseModel):
    """Phản hồi tiêu chuẩn cho việc đặt lại mật khẩu."""

    message: str
