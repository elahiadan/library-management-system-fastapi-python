from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.core.responses import success
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.common import Envelope
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=201,
    response_model=Envelope[UserOut],
    dependencies=[Depends(rate_limit(settings.register_rate_limit_per_minute))],
    summary="Register a new member account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register(db, payload)
    return success("Account created successfully", UserOut.model_validate(user))


@router.post(
    "/login",
    response_model=Envelope[TokenResponse],
    dependencies=[Depends(rate_limit(settings.login_rate_limit_per_minute))],
    summary="Authenticate and receive a JWT access token",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, payload.email, payload.password)
    token = auth_service.issue_token(user)
    data = TokenResponse(
        access_token=token, token_type="bearer", user=UserOut.model_validate(user)
    )
    return success("Login successful", data)


@router.get(
    "/me",
    response_model=Envelope[UserOut],
    summary="Get the currently authenticated user",
)
def me(current_user: User = Depends(get_current_user)):
    return success("Current user retrieved successfully", UserOut.model_validate(current_user))