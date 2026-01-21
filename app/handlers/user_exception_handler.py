from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.user import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserDisabledError,
    UserEmailSameError,
    UserNameSameError,
    UserNotFoundError,
    UserPasswordSameError,
)


def register_user_exception_handlers(app):
    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        request: Request, exc: InvalidCredentialsError
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(request: Request, exc: UserNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    @app.exception_handler(UserDisabledError)
    async def user_disabled_handler(request: Request, exc: UserDisabledError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    @app.exception_handler(EmailAlreadyExistsError)
    async def email_already_exists_handler(
        request: Request, exc: EmailAlreadyExistsError
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(UserEmailSameError)
    async def user_email_same_handler(request: Request, exc: UserEmailSameError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(UserNameSameError)
    async def user_name_same_handler(request: Request, exc: UserNameSameError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(UserPasswordSameError)
    async def user_password_same_handler(request: Request, exc: UserPasswordSameError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
