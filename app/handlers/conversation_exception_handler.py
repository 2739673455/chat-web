from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.conversation import ConversationNotFoundError


def register_conversation_exception_handlers(app):
    @app.exception_handler(ConversationNotFoundError)
    async def conversation_not_found_handler(
        request: Request, exc: ConversationNotFoundError
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )
