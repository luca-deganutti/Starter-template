from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RefreshTokenRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    return auth_service.register_user_service(db, payload)


@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    return auth_service.login_user_service(
        db,
        email=form_data.username,
        password=form_data.password,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return auth_service.refresh_token_service(db, payload.refresh_token)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
