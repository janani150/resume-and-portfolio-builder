# app/routers/ai_agent.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from agent.agent import agent   # import singleton

router = APIRouter(prefix="/agent", tags=["AI Agent"])

class ResumeInput(BaseModel):
    name: str
    role: str
    skills: List[str]
    summary: Optional[str] = None
    experience: Optional[str] = "Fresher"

class ATSInput(BaseModel):
    resume: ResumeInput
    job_description: str

# ── Analyze Resume ─────────────────────────────────────
@router.post("/analyze")
async def analyze_resume(data: ResumeInput):
    try:
        result = agent.analyze_resume(data.dict())
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── ATS Score ──────────────────────────────────────────
@router.post("/ats-score")
async def ats_score(data: ATSInput):
    try:
        result = agent.score_ats(data.resume.dict(), data.job_description)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Full Pipeline ──────────────────────────────────────
@router.post("/full-pipeline")
async def full_pipeline(data: ATSInput):
    try:
        result = agent.full_pipeline(
            data.resume.dict(),
            job_desc=data.job_description
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Health Check ───────────────────────────────────────
@router.get("/health")
async def health():
    return {"status": "AI Agent is running", "models": ["skill_extractor", "ats_scorer", "gpt2_summary", "interview_qgen"]}