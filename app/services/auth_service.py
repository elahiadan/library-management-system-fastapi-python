from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, DuplicateResource
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole

_DUMMY_HASH = get_password_hash("timing-equalizer-not-a-real-password")


def register(db: Session, payload) -> User:
    email = payload.email.lower().strip()
    existing = db.scalar(select(User).where(func.lower(User.email) == email))
    if existing is not None:
        raise DuplicateResource("Unable to register with these details")

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=get_password_hash(payload.password),
        role=UserRole.MEMBER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(func.lower(User.email) == email.lower().strip()))
    if user is None:
        verify_password(password, _DUMMY_HASH)
        raise AuthenticationError("Invalid email or password")
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise AuthenticationError("Your account is inactive")
    return user


def issue_token(user: User) -> str:
    return create_access_token(subject=str(user.id), role=user.role.value)