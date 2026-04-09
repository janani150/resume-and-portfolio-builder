"""
app/api/v1/router.py
─────────────────────
Central API v1 router — include all sub-routers here.
"""
from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.resumes import router as resume_router
from app.api.v1.endpoints.resumes import public_router
from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.pdf import router as pdf_router
from app.api.v1.endpoints.portfolios import (
    portfolio_router,
    template_router,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(resume_router)
api_router.include_router(public_router)   # /api/v1/r/{slug}
api_router.include_router(ai_router)
api_router.include_router(pdf_router)
api_router.include_router(portfolio_router)
api_router.include_router(template_router)