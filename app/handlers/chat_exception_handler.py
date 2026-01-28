from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.chat import ChatError
from app.utils.log import app_logger


def register_chat_exception_handlers(app):
    @app.exception_handler(ChatError)
    async def chat_error_handler(request: Request, exc: ChatError):
        app_logger.error(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )