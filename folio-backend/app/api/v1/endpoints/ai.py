"""
app/api/v1/endpoints/ai.py
───────────────────────────
POST /ai/enhance          — enhance / rewrite text
POST /ai/ats-check        — score resume vs job description
POST /ai/generate-summary — auto-write summary from resume data
POST /ai/suggest-skills   — suggest missing skills
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db, get_mongo_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.schemas import (
    AIEnhanceRequest,
    AIEnhanceResponse,
    ATSCheckRequest,
    ATSCheckResponse,
)
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])


# ── Text Enhancement ──────────────────────────────────────────────────────────
@router.post("/enhance", response_model=AIEnhanceResponse)
def enhance(
    body: AIEnhanceRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Rewrite a piece of resume text.
    mode: enhance | quantify | summary | keywords
    """
    try:
        result = ai_service.enhance_text(
            text=body.text,
            context=body.context or "",
            mode=body.mode,
        )
        return AIEnhanceResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )


# ── ATS Check ─────────────────────────────────────────────────────────────────
@router.post("/ats-check", response_model=ATSCheckResponse)
async def ats_check(
    body: ATSCheckRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Score a resume against a job description."""
    # Fetch resume
    resume = db.query(Resume).filter(
        Resume.id == body.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_data = {}
    if resume.mongo_doc_id:
        from bson import ObjectId
        doc = await mongo["resume_data"].find_one(
            {"_id": ObjectId(resume.mongo_doc_id)}
        )
        if doc:
            doc["_id"] = str(doc["_id"])
            resume_data = doc

    try:
        result = ai_service.check_ats(resume_data, body.job_description)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    # Persist score back to resume row
    resume.ats_score = result["score"]
    db.commit()

    return ATSCheckResponse(**result)


# ── Generate Summary ──────────────────────────────────────────────────────────
@router.post("/generate-summary")
async def generate_summary(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Auto-generate a professional summary from a resume's data."""
    resume_id = body.get("resume_id")
    if not resume_id:
        raise HTTPException(status_code=422, detail="resume_id required")

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_data = {}
    if resume.mongo_doc_id:
        from bson import ObjectId
        doc = await mongo["resume_data"].find_one(
            {"_id": ObjectId(resume.mongo_doc_id)}
        )
        if doc:
            resume_data = doc

    try:
        summary = ai_service.generate_summary(resume_data)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")


# ── Suggest Skills ────────────────────────────────────────────────────────────
@router.post("/suggest-skills")
async def suggest_skills(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Suggest additional skills based on existing profile."""
    resume_id = body.get("resume_id")
    job_description = body.get("job_description", "")

    resume_data = {}
    if resume_id:
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == current_user.id,
        ).first()
        if resume and resume.mongo_doc_id:
            from bson import ObjectId
            doc = await mongo["resume_data"].find_one(
                {"_id": ObjectId(resume.mongo_doc_id)}
            )
            if doc:
                resume_data = doc

    try:
        skills = ai_service.suggest_skills(resume_data, job_description)
        return {"skills": skills}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")