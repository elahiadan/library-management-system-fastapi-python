from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.dependencies.permissions import require_admin
from app.schemas.common import Envelope, ErrorResponse, build_page_meta
from app.schemas.user import UserListOut, UserOut
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])

ADMIN_ERRORS = {403: {"model": ErrorResponse}, 401: {"model": ErrorResponse}}


@router.get(
    "",
    response_model=Envelope[UserListOut],
    dependencies=[Depends(require_admin)],
    responses=ADMIN_ERRORS,
    summary="List all users (admin only)",
)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    users, total = user_service.list_users(db, page, page_size)
    return success(
        "Users retrieved successfully",
        UserListOut(
            items=[UserOut.model_validate(u) for u in users],
            meta=build_page_meta(page, page_size, total),
        ),
    )


@router.get(
    "/{user_id}",
    response_model=Envelope[UserOut],
    dependencies=[Depends(require_admin)],
    responses=ADMIN_ERRORS,
    summary="Get a user by id (admin only)",
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = user_service.get_user(db, user_id)
    return success("User retrieved successfully", UserOut.model_validate(user))