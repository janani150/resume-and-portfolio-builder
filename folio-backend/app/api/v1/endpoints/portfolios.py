"""
app/api/v1/endpoints/portfolios.py  &  templates.py
─────────────────────────────────────────────────────
Portfolio CRUD:
  GET    /portfolios
  POST   /portfolios
  GET    /portfolios/{id}
  PUT    /portfolios/{id}
  DELETE /portfolios/{id}
  POST   /portfolios/{id}/publish

Templates:
  GET  /templates?kind=resume|portfolio
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db, get_mongo_db
from app.models.portfolio import Portfolio
from app.models.resume import Resume
from app.models.template import Template
from app.models.user import User
from app.schemas.schemas import (
    MessageResponse,
    PortfolioCreateRequest,
    PortfolioDetailOut,
    PortfolioOut,
    PortfolioUpdateRequest,
    TemplateOut,
)

# ─────────────────────────────────────────────────────────────────────────────
# Portfolios
# ─────────────────────────────────────────────────────────────────────────────
portfolio_router = APIRouter(prefix="/portfolios", tags=["Portfolios"])
MONGO_PORTFOLIO = "portfolio_data"


@portfolio_router.get("", response_model=List[PortfolioOut])
def list_portfolios(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id)
        .order_by(Portfolio.updated_at.desc())
        .all()
    )


@portfolio_router.post("", response_model=PortfolioOut, status_code=201)
async def create_portfolio(
    body: PortfolioCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    # Seed from resume if provided
    portfolio_doc: dict = {}
    if body.resume_id:
        resume = db.query(Resume).filter(
            Resume.id == body.resume_id,
            Resume.user_id == current_user.id,
        ).first()
        if resume and resume.mongo_doc_id:
            from bson import ObjectId
            doc = await mongo["resume_data"].find_one(
                {"_id": ObjectId(resume.mongo_doc_id)}
            )
            if doc:
                doc["_id"] = str(doc["_id"])
                portfolio_doc = {"resume_data": doc, "customisation": {}}

    portfolio_doc["user_id"] = current_user.id
    portfolio_doc["template_id"] = body.template_id
    result = await mongo[MONGO_PORTFOLIO].insert_one(portfolio_doc)

    portfolio = Portfolio(
        user_id=current_user.id,
        title=body.title,
        template_id=body.template_id,
        mongo_doc_id=str(result.inserted_id),
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@portfolio_router.get("/{portfolio_id}", response_model=PortfolioDetailOut)
async def get_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    portfolio = _get_portfolio_or_404(portfolio_id, current_user.id, db)
    data = await _load_mongo(portfolio.mongo_doc_id, mongo)
    out = PortfolioDetailOut.model_validate(portfolio)
    out.data = data
    return out


@portfolio_router.put("/{portfolio_id}", response_model=PortfolioOut)
async def update_portfolio(
    portfolio_id: str,
    body: PortfolioUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    portfolio = _get_portfolio_or_404(portfolio_id, current_user.id, db)

    if body.title is not None:
        portfolio.title = body.title
    if body.template_id is not None:
        portfolio.template_id = body.template_id
    if body.is_published is not None:
        portfolio.is_published = body.is_published
    if body.subdomain is not None:
        # Check subdomain uniqueness
        exists = db.query(Portfolio).filter(
            Portfolio.subdomain == body.subdomain,
            Portfolio.id != portfolio.id,
        ).first()
        if exists:
            raise HTTPException(status_code=409, detail="Subdomain already taken")
        portfolio.subdomain = body.subdomain

    if body.customisation is not None and portfolio.mongo_doc_id:
        from bson import ObjectId
        await mongo[MONGO_PORTFOLIO].update_one(
            {"_id": ObjectId(portfolio.mongo_doc_id)},
            {"$set": {"customisation": body.customisation}},
        )

    db.commit()
    db.refresh(portfolio)
    return portfolio


@portfolio_router.delete("/{portfolio_id}", response_model=MessageResponse)
async def delete_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    portfolio = _get_portfolio_or_404(portfolio_id, current_user.id, db)

    if portfolio.mongo_doc_id:
        from bson import ObjectId
        await mongo[MONGO_PORTFOLIO].delete_one(
            {"_id": ObjectId(portfolio.mongo_doc_id)}
        )

    db.delete(portfolio)
    db.commit()
    return MessageResponse(message="Portfolio deleted")


@portfolio_router.post("/{portfolio_id}/publish", response_model=PortfolioOut)
def publish_portfolio(
    portfolio_id: str,
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    portfolio = _get_portfolio_or_404(portfolio_id, current_user.id, db)
    subdomain = body.get("subdomain")
    if subdomain:
        exists = db.query(Portfolio).filter(
            Portfolio.subdomain == subdomain,
            Portfolio.id != portfolio.id,
        ).first()
        if exists:
            raise HTTPException(status_code=409, detail="Subdomain already taken")
        portfolio.subdomain = subdomain

    portfolio.is_published = True
    db.commit()
    db.refresh(portfolio)
    return portfolio


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_portfolio_or_404(portfolio_id: str, user_id: str, db: Session) -> Portfolio:
    p = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p


async def _load_mongo(mongo_id: Optional[str], mongo) -> Optional[dict]:
    if not mongo_id:
        return None
    from bson import ObjectId
    doc = await mongo[MONGO_PORTFOLIO].find_one({"_id": ObjectId(mongo_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ─────────────────────────────────────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────────────────────────────────────
template_router = APIRouter(prefix="/templates", tags=["Templates"])

# Seed data (in prod, these come from DB)
_SEED_TEMPLATES = [
    {"id": "modern", "name": "Modern Clean", "kind": "resume", "is_free": True, "tags": "minimal,free", "thumbnail_url": None},
    {"id": "midnight", "name": "Midnight", "kind": "resume", "is_free": True, "tags": "dark,minimal,free", "thumbnail_url": None},
    {"id": "classic", "name": "Classic Professional", "kind": "resume", "is_free": True, "tags": "classic,free", "thumbnail_url": None},
    {"id": "creative-sidebar", "name": "Creative Sidebar", "kind": "resume", "is_free": False, "tags": "creative", "thumbnail_url": None},
    {"id": "executive-gold", "name": "Executive Gold", "kind": "resume", "is_free": False, "tags": "classic,minimal", "thumbnail_url": None},
    {"id": "bold-dark", "name": "Bold Dark", "kind": "resume", "is_free": False, "tags": "dark,creative", "thumbnail_url": None},
    {"id": "clean-minimal", "name": "Clean Minimal", "kind": "portfolio", "is_free": True, "tags": "minimal,free", "thumbnail_url": None},
    {"id": "dark-terminal", "name": "Dark Terminal", "kind": "portfolio", "is_free": True, "tags": "dark,free", "thumbnail_url": None},
    {"id": "editorial", "name": "Editorial", "kind": "portfolio", "is_free": False, "tags": "creative", "thumbnail_url": None},
    {"id": "glass-morph", "name": "Glass Morph", "kind": "portfolio", "is_free": False, "tags": "creative", "thumbnail_url": None},
    {"id": "brutalist", "name": "Brutalist", "kind": "portfolio", "is_free": False, "tags": "bold,creative", "thumbnail_url": None},
]


@template_router.get("", response_model=List[TemplateOut])
def list_templates(
    kind: Optional[str] = Query(None, pattern="^(resume|portfolio)$"),
    free_only: bool = Query(False),
):
    results = _SEED_TEMPLATES
    if kind:
        results = [t for t in results if t["kind"] == kind]
    if free_only:
        results = [t for t in results if t["is_free"]]
    return [TemplateOut(**t) for t in results]


@template_router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: str):
    for t in _SEED_TEMPLATES:
        if t["id"] == template_id:
            return TemplateOut(**t)
    raise HTTPException(status_code=404, detail="Template not found")