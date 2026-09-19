import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import exceptions
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise exceptions.AuthenticationError("Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        raise exceptions.AuthenticationError("Invalid or expired token")

    user = db.get(User, user_id)
    if user is None:
        raise exceptions.AuthenticationError("User no longer exists")
    if not user.is_active:
        raise exceptions.AuthenticationError("Inactive account")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user