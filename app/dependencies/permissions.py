from fastapi import Depends

from app.core.exceptions import AuthorizationError
from app.dependencies.auth import get_current_active_user
from app.models.user import User, UserRole


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    return current_user


def require_member(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.MEMBER:
        raise AuthorizationError("Member access required")
    return current_user