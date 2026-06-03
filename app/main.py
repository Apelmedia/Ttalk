from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

import app.models  # noqa: F401
from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.db import Base, engine


def normalized_origins(raw_origins: str) -> list[str]:
    return list(dict.fromkeys(origin.strip() for origin in raw_origins.split(",") if origin.strip()))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Warm Haven 안전 매칭·채팅 앱 백엔드 초안",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=normalized_origins(settings.ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(v1_router, prefix="/v1")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "warm-haven",
        "environment": settings.ENVIRONMENT,
        "demo_mode": settings.DEMO_MODE,
    }


static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
