"""
app/api/v1/endpoints/resumes.py
────────────────────────────────
GET    /resumes              — list user's resumes
POST   /resumes              — create resume
GET    /resumes/{id}         — get with full data
PUT    /resumes/{id}         — update
DELETE /resumes/{id}         — delete
POST   /resumes/{id}/clone   — duplicate
GET    /r/{slug}             — public share link
"""
from __future__ import annotations

import random
import string
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db, get_mongo_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.schemas import (
    MessageResponse,
    ResumeCreateRequest,
    ResumeDetailOut,
    ResumeOut,
    ResumeUpdateRequest,
)

router = APIRouter(prefix="/resumes", tags=["Resumes"])
MONGO_COLLECTION = "resume_data"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_resume_or_404(resume_id: str, user_id: str, db: Session) -> Resume:
    r = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id,
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resume not found")
    return r


def _random_slug(length: int = 10) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


# ── List ──────────────────────────────────────────────────────────────────────
@router.get("", response_model=List[ResumeOut])
def list_resumes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.updated_at.desc())
        .all()
    )


# ── Create ────────────────────────────────────────────────────────────────────
@router.post("", response_model=ResumeOut, status_code=201)
async def create_resume(
    body: ResumeCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    # Free plan limit: max 1 resume
    if current_user.plan == "free":
        count = db.query(Resume).filter(Resume.user_id == current_user.id).count()
        if count >= 1:
            raise HTTPException(
                status_code=402,
                detail="Free plan allows 1 resume. Upgrade to Pro for unlimited.",
            )

    # Save data to MongoDB
    doc = body.data.model_dump()
    doc["user_id"] = current_user.id
    result = await mongo[MONGO_COLLECTION].insert_one(doc)
    mongo_id = str(result.inserted_id)

    resume = Resume(
        user_id=current_user.id,
        title=body.title,
        mongo_doc_id=mongo_id,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


# ── Get Detail ────────────────────────────────────────────────────────────────
@router.get("/{resume_id}", response_model=ResumeDetailOut)
async def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    resume = _get_resume_or_404(resume_id, current_user.id, db)

    data = None
    if resume.mongo_doc_id:
        from bson import ObjectId
        doc = await mongo[MONGO_COLLECTION].find_one(
            {"_id": ObjectId(resume.mongo_doc_id)}
        )
        if doc:
            doc["_id"] = str(doc["_id"])
            data = doc

    out = ResumeDetailOut.model_validate(resume)
    out.data = data
    return out


# ── Update ────────────────────────────────────────────────────────────────────
@router.put("/{resume_id}", response_model=ResumeDetailOut)
async def update_resume(
    resume_id: str,
    body: ResumeUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    resume = _get_resume_or_404(resume_id, current_user.id, db)

    if body.title is not None:
        resume.title = body.title
    if body.template_id is not None:
        resume.template_id = body.template_id
    if body.is_public is not None:
        resume.is_public = body.is_public
        if body.is_public and not resume.public_slug:
            resume.public_slug = _random_slug()

    if body.data is not None and resume.mongo_doc_id:
        from bson import ObjectId
        await mongo[MONGO_COLLECTION].update_one(
            {"_id": ObjectId(resume.mongo_doc_id)},
            {"$set": body.data.model_dump()},
        )

    db.commit()
    db.refresh(resume)

    out = ResumeDetailOut.model_validate(resume)
    if body.data:
        out.data = body.data.model_dump()
    return out


# ── Delete ────────────────────────────────────────────────────────────────────
@router.delete("/{resume_id}", response_model=MessageResponse)
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    resume = _get_resume_or_404(resume_id, current_user.id, db)

    if resume.mongo_doc_id:
        from bson import ObjectId
        await mongo[MONGO_COLLECTION].delete_one(
            {"_id": ObjectId(resume.mongo_doc_id)}
        )

    db.delete(resume)
    db.commit()
    return MessageResponse(message="Resume deleted")


# ── Clone ─────────────────────────────────────────────────────────────────────
@router.post("/{resume_id}/clone", response_model=ResumeOut, status_code=201)
async def clone_resume(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    original = _get_resume_or_404(resume_id, current_user.id, db)

    new_mongo_id = None
    if original.mongo_doc_id:
        from bson import ObjectId
        doc = await mongo[MONGO_COLLECTION].find_one(
            {"_id": ObjectId(original.mongo_doc_id)}
        )
        if doc:
            doc.pop("_id", None)
            result = await mongo[MONGO_COLLECTION].insert_one(doc)
            new_mongo_id = str(result.inserted_id)

    clone = Resume(
        user_id=current_user.id,
        title=f"{original.title} (Copy)",
        template_id=original.template_id,
        mongo_doc_id=new_mongo_id,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone


# ── Public share link ─────────────────────────────────────────────────────────
public_router = APIRouter(tags=["Public"])


@public_router.get("/r/{slug}", response_model=ResumeDetailOut)
async def public_resume(
    slug: str,
    db: Session = Depends(get_db),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    resume = db.query(Resume).filter(
        Resume.public_slug == slug,
        Resume.is_public == True,  # noqa: E712
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found or not public")

    data = None
    if resume.mongo_doc_id:
        from bson import ObjectId
        doc = await mongo[MONGO_COLLECTION].find_one(
            {"_id": ObjectId(resume.mongo_doc_id)}
        )
        if doc:
            doc["_id"] = str(doc["_id"])
            data = doc

    out = ResumeDetailOut.model_validate(resume)
    out.data = data
    return out