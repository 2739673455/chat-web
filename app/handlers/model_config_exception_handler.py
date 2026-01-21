from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.model_config import ModelConfigNotFoundError


def register_model_config_exception_handlers(app):
    @app.exception_handler(ModelConfigNotFoundError)
    async def model_config_not_found_handler(
        request: Request, exc: ModelConfigNotFoundError
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )
