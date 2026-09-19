class AppError(Exception):
    status_code: int = 500
    message: str = "Something went wrong"
    errors: dict | None = None

    def __init__(
        self,
        message: str | None = None,
        errors: dict | None = None,
        status_code: int | None = None,
    ):
        self.message = message or self.message
        self.errors = errors
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFound(AppError):
    status_code = 404
    message = "Resource not found"


class AuthenticationError(AppError):
    status_code = 401
    message = "Authentication failed"


class AuthorizationError(AppError):
    status_code = 403
    message = "You do not have permission to perform this action"


class DuplicateResource(AppError):
    status_code = 409
    message = "Resource already exists"


class BookUnavailable(AppError):
    status_code = 409
    message = "No copies of this book are currently available"


class BorrowingLimitExceeded(AppError):
    status_code = 409
    message = "Borrowing limit exceeded"


class InvalidBorrowingState(AppError):
    status_code = 409
    message = "Invalid borrowing state"