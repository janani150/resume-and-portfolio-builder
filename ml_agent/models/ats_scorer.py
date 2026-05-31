# models/ats_scorer.py
"""
Model: Sentence-BERT (all-MiniLM-L6-v2)
Task: Compare resume vs job description → ATS score (0-100)
No training needed — uses pretrained BERT embeddings
"""
import numpy as np
from sentence_transformers import SentenceTransformer, util
from preprocessing.cleaner import clean_text

model = SentenceTransformer('all-MiniLM-L6-v2')

# ── Keyword Match Score ────────────────────────────────
def keyword_match_score(resume_text: str, job_desc: str) -> dict:
    job_words = set(job_desc.lower().split())
    resume_words = set(resume_text.lower().split())
    
    matched = job_words & resume_words
    missing = job_words - resume_words
    
    score = len(matched) / len(job_words) * 100 if job_words else 0
    return {
        "keyword_score": round(score, 2),
        "matched_keywords": list(matched)[:10],
        "missing_keywords": list(missing)[:10]
    }

# ── Semantic Similarity Score ──────────────────────────
def semantic_similarity_score(resume_text: str, job_desc: str) -> float:
    resume_clean = clean_text(resume_text)
    job_clean = clean_text(job_desc)
    
    emb_resume = model.encode(resume_clean, convert_to_tensor=True)
    emb_job = model.encode(job_clean, convert_to_tensor=True)
    
    similarity = util.cos_sim(emb_resume, emb_job)
    return round(float(similarity[0][0]) * 100, 2)

# ── Final ATS Score ────────────────────────────────────
def calculate_ats_score(resume: dict, job_desc: str) -> dict:
    resume_text = ' '.join([
        resume.get('summary', ''),
        ' '.join(resume.get('skills', [])),
        resume.get('role', '')
    ])
    
    keyword_result = keyword_match_score(resume_text, job_desc)
    semantic_score = semantic_similarity_score(resume_text, job_desc)
    
    # Weighted final score
    final_score = (keyword_result['keyword_score'] * 0.4 + semantic_score * 0.6)
    
    tips = []
    if final_score < 60:
        tips.append("Add more keywords from the job description")
    if len(keyword_result['missing_keywords']) > 5:
        tips.append(f"Missing key terms: {', '.join(keyword_result['missing_keywords'][:3])}")
    if semantic_score < 50:
        tips.append("Rewrite summary to better match the job role")
    if not tips:
        tips.append("Great match! Your resume aligns well with this job.")
    
    return {
        "ats_score": round(final_score, 2),
        "keyword_score": keyword_result['keyword_score'],
        "semantic_score": semantic_score,
        "matched_keywords": keyword_result['matched_keywords'],
        "missing_keywords": keyword_result['missing_keywords'],
        "improvement_tips": tips
    }

if __name__ == "__main__":
    resume = {
        "summary": "Python developer with FastAPI and MongoDB experience",
        "skills": ["Python", "FastAPI", "MongoDB", "React"],
        "role": "Backend Developer"
    }
    job = "Looking for a Python backend developer with REST API and NoSQL experience"
    result = calculate_ats_score(resume, job)
    print(result)