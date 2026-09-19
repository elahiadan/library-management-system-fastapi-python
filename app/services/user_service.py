from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFound
from app.models.user import User


def list_users(db: Session, page: int, page_size: int):
    query = select(User)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    users = db.scalars(
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return users, total


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ResourceNotFound(f"User with id {user_id} not found")
    return user