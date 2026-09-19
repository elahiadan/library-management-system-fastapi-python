from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import require_admin
from app.models.user import User
from app.schemas.author import AuthorCreate, AuthorListOut, AuthorOut, AuthorUpdate
from app.schemas.common import Envelope, ErrorResponse, build_page_meta
from app.services import author_service

router = APIRouter(prefix="/authors", tags=["Authors"])

ADMIN_ERRORS = {403: {"model": ErrorResponse}, 401: {"model": ErrorResponse}}
NOT_FOUND_ERRORS = {404: {"model": ErrorResponse}, **ADMIN_ERRORS}


@router.get(
    "",
    response_model=Envelope[AuthorListOut],
    responses=NOT_FOUND_ERRORS,
    summary="List authors (authenticated users)",
)
def list_authors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    authors, total = author_service.list_authors(db, page, page_size, search)
    return success(
        "Authors retrieved successfully",
        AuthorListOut(
            items=[AuthorOut.model_validate(a) for a in authors],
            meta=build_page_meta(page, page_size, total),
        ),
    )


@router.get(
    "/{author_id}",
    response_model=Envelope[AuthorOut],
    responses=NOT_FOUND_ERRORS,
    summary="Get an author by id (authenticated users)",
)
def get_author(
    author_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    author = author_service.get_author(db, author_id)
    return success("Author retrieved successfully", AuthorOut.model_validate(author))


@router.post(
    "",
    status_code=201,
    response_model=Envelope[AuthorOut],
    dependencies=[Depends(require_admin)],
    responses=NOT_FOUND_ERRORS,
    summary="Create an author (admin only)",
)
def create_author(payload: AuthorCreate, db: Session = Depends(get_db)):
    author = author_service.create_author(db, payload)
    return success("Author created successfully", AuthorOut.model_validate(author))


@router.put(
    "/{author_id}",
    response_model=Envelope[AuthorOut],
    dependencies=[Depends(require_admin)],
    responses=NOT_FOUND_ERRORS,
    summary="Update an author (admin only)",
)
def update_author(
    author_id: int, payload: AuthorUpdate, db: Session = Depends(get_db)
):
    author = author_service.update_author(db, author_id, payload)
    return success("Author updated successfully", AuthorOut.model_validate(author))


@router.delete(
    "/{author_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
    responses=NOT_FOUND_ERRORS,
    summary="Delete an author (admin only)",
)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author_service.delete_author(db, author_id)
    return Response(status_code=204)