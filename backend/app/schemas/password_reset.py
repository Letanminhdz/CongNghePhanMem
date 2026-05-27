"""
Password reset API schemas.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class ForgotPasswordRequest(BaseModel):
    """Forgot password request payload."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request payload."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetResponse(BaseModel):
    """Standard password reset response."""

    message: str
