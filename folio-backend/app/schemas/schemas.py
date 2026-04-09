"""
app/schemas/schemas.py
───────────────────────
All Pydantic v2 request / response schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    plan: str
    is_verified: bool
    avatar_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Resume — Info (stored in MongoDB)
# ─────────────────────────────────────────────────────────────────────────────
class ContactInfo(BaseModel):
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: Optional[str] = None


class WorkExperience(BaseModel):
    job_title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None   # "YYYY-MM"
    end_date: Optional[str] = None     # "YYYY-MM" or "Present"
    description: str = ""              # bullet points / achievements


class Education(BaseModel):
    institution: str
    degree: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[str] = None
    achievements: Optional[str] = None


class Project(BaseModel):
    name: str
    tech_stack: Optional[str] = None
    link: Optional[str] = None
    description: str = ""


class ResumeData(BaseModel):
    """Full resume payload saved to MongoDB."""
    first_name: str
    last_name: str
    professional_title: str
    email: EmailStr
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    experience: List[WorkExperience] = []
    education: List[Education] = []
    skills: List[str] = []
    projects: List[Project] = []


class ResumeCreateRequest(BaseModel):
    title: str = "My Resume"
    data: ResumeData


class ResumeUpdateRequest(BaseModel):
    title: Optional[str] = None
    template_id: Optional[str] = None
    data: Optional[ResumeData] = None
    is_public: Optional[bool] = None


class ResumeOut(BaseModel):
    id: str
    title: str
    template_id: Optional[str]
    ats_score: Optional[float]
    is_public: bool
    public_slug: Optional[str]
    pdf_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeDetailOut(ResumeOut):
    data: Optional[Dict[str, Any]] = None   # full resume JSON from MongoDB


# ─────────────────────────────────────────────────────────────────────────────
# AI Enhancement
# ─────────────────────────────────────────────────────────────────────────────
class AIEnhanceRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=5000)
    context: Optional[str] = None      # e.g. "job description"
    mode: str = Field(
        default="enhance",
        pattern="^(enhance|quantify|summary|keywords|ats_check)$"
    )


class AIEnhanceResponse(BaseModel):
    original: str
    enhanced: str
    suggestions: List[str] = []
    keywords: List[str] = []
    ats_score: Optional[float] = None


class ATSCheckRequest(BaseModel):
    resume_id: str
    job_description: str = Field(..., min_length=50)


class ATSCheckResponse(BaseModel):
    score: float                        # 0–100
    matched_keywords: List[str]
    missing_keywords: List[str]
    suggestions: List[str]


# ─────────────────────────────────────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────────────────────────────────────
class TemplateOut(BaseModel):
    id: str
    name: str
    kind: str
    thumbnail_url: Optional[str]
    tags: List[str]
    is_free: bool

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def split_tags(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio
# ─────────────────────────────────────────────────────────────────────────────
class PortfolioCreateRequest(BaseModel):
    title: str = "My Portfolio"
    template_id: str
    resume_id: Optional[str] = None   # seed data from existing resume


class PortfolioUpdateRequest(BaseModel):
    title: Optional[str] = None
    template_id: Optional[str] = None
    customisation: Optional[Dict[str, Any]] = None
    is_published: Optional[bool] = None
    subdomain: Optional[str] = Field(None, pattern=r"^[a-z0-9\-]{3,50}$")


class PortfolioOut(BaseModel):
    id: str
    title: str
    template_id: str
    is_published: bool
    subdomain: Optional[str]
    custom_domain: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PortfolioDetailOut(PortfolioOut):
    data: Optional[Dict[str, Any]] = None   # full portfolio config from MongoDB


# ─────────────────────────────────────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────────────────────────────────────
class PDFGenerateRequest(BaseModel):
    resume_id: str
    template_id: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Generic
# ─────────────────────────────────────────────────────────────────────────────
class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None