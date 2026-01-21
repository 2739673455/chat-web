import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import CFG
from app.dependencies.database import db_manager
from app.handlers import register_exception_handlers
from app.routers.api import api


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db_manager.close_all()


app = FastAPI(lifespan=lifespan)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CFG.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理
register_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(api.router)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=CFG.port,
        reload=True,
        reload_dirs=[os.path.dirname(__file__)],
    )
