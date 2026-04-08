from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.routes import customer, otp, prize, health, qr, admin
from app.core.logger import get_logger

logger = get_logger("main")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NIRVIZ Resort API starting up...")
    yield
    logger.info("NIRVIZ Resort API shutting down.")
    await engine.dispose()


app = FastAPI(
    title="NIRVIZ Resort — Customer Registration API",
    version="1.0.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(otp.router,      prefix="/api/v1/otp",      tags=["OTP"])
app.include_router(customer.router, prefix="/api/v1/customer", tags=["Customer"])
app.include_router(prize.router,    prefix="/api/v1/prize",    tags=["Prize"])
app.include_router(qr.router,       prefix="/api/v1",          tags=["QR Code"])
app.include_router(admin.router,    prefix="/api/v1/admin",    tags=["Admin"])
