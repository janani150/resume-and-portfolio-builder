"""
app/services/ai_service.py
───────────────────────────
All Claude (Anthropic) AI calls:
  - enhance_text       →  rewrite bullet points / summary
  - check_ats          →  score resume against job description
  - suggest_keywords   →  extract missing keywords
  - generate_summary   →  write professional summary from data
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import anthropic

from app.core.config import settings

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
MODEL = "claude-sonnet-4-20250514"


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────
def _chat(system: str, user: str, max_tokens: int = 1024) -> str:
    msg = _client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


def _json_chat(system: str, user: str, max_tokens: int = 1024) -> Dict[str, Any]:
    """Call Claude and parse the JSON response."""
    raw = _chat(system, user, max_tokens)
    # Strip markdown fences if present
    clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    return json.loads(clean)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def enhance_text(text: str, context: str = "", mode: str = "enhance") -> Dict[str, Any]:
    """
    Rewrite resume text to be stronger.
    mode: enhance | quantify | summary | keywords
    """
    system = (
        "You are an expert resume writer and career coach. "
        "You specialise in writing powerful, ATS-optimised bullet points "
        "that are quantified, action-verb-led, and result-focused. "
        "Always respond ONLY with valid JSON, no markdown, no preamble."
    )

    mode_instructions = {
        "enhance": (
            "Rewrite the following resume text to be stronger, more impactful, "
            "and professional. Use strong action verbs and improve clarity."
        ),
        "quantify": (
            "Add realistic quantitative metrics (%, numbers, timeframes) "
            "to make the statements more impactful. If you cannot add real numbers, "
            "suggest [X%] or [N users] placeholders."
        ),
        "summary": (
            "Rewrite this as a polished 2-4 sentence professional summary "
            "suitable for the top of a resume."
        ),
        "keywords": (
            "Extract important technical and soft skill keywords from this text "
            "that would help with ATS systems."
        ),
    }

    instruction = mode_instructions.get(mode, mode_instructions["enhance"])
    context_line = f"\nJob context: {context}" if context else ""

    prompt = f"""
{instruction}{context_line}

Original text:
{text}

Respond ONLY with this JSON structure:
{{
  "enhanced": "<improved text>",
  "suggestions": ["<tip 1>", "<tip 2>"],
  "keywords": ["<keyword1>", "<keyword2>"]
}}
"""
    result = _json_chat(system, prompt, max_tokens=1500)
    return {
        "original": text,
        "enhanced": result.get("enhanced", text),
        "suggestions": result.get("suggestions", []),
        "keywords": result.get("keywords", []),
        "ats_score": None,
    }


def check_ats(resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    Score resume against a job description.
    Returns score (0-100), matched/missing keywords, and suggestions.
    """
    system = (
        "You are an ATS (Applicant Tracking System) expert. "
        "Analyse resumes against job descriptions and provide actionable feedback. "
        "Respond ONLY with valid JSON."
    )

    resume_text = _flatten_resume(resume_data)

    prompt = f"""
Analyse this resume against the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Respond ONLY with this JSON:
{{
  "score": <integer 0-100>,
  "matched_keywords": ["<kw1>", "<kw2>"],
  "missing_keywords": ["<kw1>", "<kw2>"],
  "suggestions": ["<actionable suggestion 1>", "<actionable suggestion 2>"]
}}
"""
    result = _json_chat(system, prompt, max_tokens=1200)
    return {
        "score": float(result.get("score", 50)),
        "matched_keywords": result.get("matched_keywords", []),
        "missing_keywords": result.get("missing_keywords", []),
        "suggestions": result.get("suggestions", []),
    }


def generate_summary(resume_data: Dict[str, Any]) -> str:
    """
    Auto-generate a professional summary from resume data.
    """
    system = (
        "You are a professional resume writer. "
        "Write concise, impactful professional summaries. "
        "Respond with plain text only — no JSON, no markdown."
    )

    name = f"{resume_data.get('first_name', '')} {resume_data.get('last_name', '')}".strip()
    title = resume_data.get("professional_title", "")
    skills = ", ".join(resume_data.get("skills", [])[:10])
    experience = resume_data.get("experience", [])
    exp_summary = ""
    if experience:
        first = experience[0]
        exp_summary = (
            f"Most recent role: {first.get('job_title')} at {first.get('company')}. "
            f"Description: {first.get('description', '')[:300]}"
        )

    prompt = f"""
Write a 2-4 sentence professional summary for a resume.

Name: {name}
Title: {title}
Key skills: {skills}
{exp_summary}

Write the summary directly, no labels or headers.
"""
    return _chat(system, prompt, max_tokens=300)


def suggest_skills(resume_data: Dict[str, Any], job_description: str = "") -> List[str]:
    """Suggest additional skills to add based on existing profile + optional JD."""
    system = (
        "You are a tech career advisor. "
        "Suggest relevant skills to add to a developer's resume. "
        "Respond ONLY with a JSON array of skill strings."
    )

    current_skills = resume_data.get("skills", [])
    title = resume_data.get("professional_title", "developer")
    jd_line = f"\nTarget job description: {job_description[:500]}" if job_description else ""

    prompt = f"""
Current role: {title}
Current skills: {", ".join(current_skills)}{jd_line}

Suggest 5-8 additional skills that would complement this profile and improve ATS matching.
Respond ONLY with a JSON array: ["skill1", "skill2", ...]
"""
    raw = _chat(system, prompt, max_tokens=300)
    clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Internal utility
# ─────────────────────────────────────────────────────────────────────────────
def _flatten_resume(data: Dict[str, Any]) -> str:
    """Convert resume dict to plain text for ATS analysis."""
    parts = []

    if data.get("professional_title"):
        parts.append(data["professional_title"])
    if data.get("summary"):
        parts.append(data["summary"])

    for exp in data.get("experience", []):
        parts.append(
            f"{exp.get('job_title')} at {exp.get('company')}: {exp.get('description', '')}"
        )

    for edu in data.get("education", []):
        parts.append(f"{edu.get('degree')} from {edu.get('institution')}")

    skills = data.get("skills", [])
    if skills:
        parts.append("Skills: " + ", ".join(skills))

    for proj in data.get("projects", []):
        parts.append(
            f"Project: {proj.get('name')} ({proj.get('tech_stack', '')}): "
            f"{proj.get('description', '')}"
        )

    return "\n".join(parts)