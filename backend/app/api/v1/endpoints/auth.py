import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.repositories import user_repository
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    PasswordResetResponse,
    ResetPasswordRequest,
)
from app.schemas.token import Token

from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    OAuth2 compatible token login, retrieve an access token for future requests.
    """
    user = user_repository.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        logger.warning(f"Failed login attempt for email={form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        logger.warning(f"Inactive user login attempt for user_id={user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.info(f"Successful login for user_id={user.id}")
    return Token(access_token=access_token, token_type="bearer")


@router.post("/forgot-password", response_model=PasswordResetResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user = user_repository.get_user_by_email(db, email=request.email)
    if user:
        token = generate_password_reset_token(user.email)
        logger.info(f"Reset token for {user.email}: {token}")
        if settings.emails_enabled:
            email_data = generate_reset_password_email(
                email_to=user.email,
                email=user.email,
                token=token,
            )
            try:
                send_email(
                    email_to=user.email,
                    subject=email_data.subject,
                    html_content=email_data.html_content,
                )
            except Exception as exc:
                logger.warning(f"Password reset email could not be sent: {exc}")
    
    # Always return success message for security
    return PasswordResetResponse(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    user = user_repository.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user_repository.update_user_password(db, user, request.new_password)
    logger.info(f"Password reset success for user_id={user.id}")
    return PasswordResetResponse(message="Password updated successfully")
