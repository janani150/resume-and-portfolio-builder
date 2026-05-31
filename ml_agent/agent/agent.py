# agent/agent.py
"""
The AI Agent — orchestrates all 4 ML models
Single entry point for all AI operations
"""
import pickle
from models.skill_extractor import predict_role, extract_skills
from models.ats_scorer import calculate_ats_score
from models.summary_generator import generate_summary
from models.interview_qgen import generate_questions
from preprocessing.cleaner import clean_text

class ResumeAgent:
    def __init__(self):
        print("Loading AI Agent...")
        # Load trained models
        with open("data/models/skill_extractor.pkl", 'rb') as f:
            self.classifier = pickle.load(f)
        with open("data/models/tfidf.pkl", 'rb') as f:
            from preprocessing.vectorizer import TFIDFVectorizer
            self.vectorizer = TFIDFVectorizer()
            self.vectorizer.load()
        print("Agent ready!")

    def analyze_resume(self, resume: dict) -> dict:
        """Full resume analysis pipeline"""
        resume_text = ' '.join([
            resume.get('summary', ''),
            ' '.join(resume.get('skills', [])),
            resume.get('role', '')
        ])

        # 1. Classify role
        role_result = predict_role(
            resume_text, self.classifier, self.vectorizer
        )

        # 2. Generate summary if not provided
        if not resume.get('summary'):
            summary = generate_summary(
                skills=resume.get('skills', []),
                role=resume.get('role', role_result['predicted_role']),
                experience=resume.get('experience', 'Fresher')
            )
        else:
            summary = resume['summary']

        # 3. Generate interview questions
        questions = generate_questions(
            skills=resume.get('skills', []),
            role=resume.get('role', '')
        )

        return {
            "predicted_role": role_result['predicted_role'],
            "confidence": role_result['confidence'],
            "extracted_skills": role_result['extracted_skills'],
            "generated_summary": summary,
            "interview_questions": questions,
        }

    def score_ats(self, resume: dict, job_desc: str) -> dict:
        """ATS scoring pipeline"""
        return calculate_ats_score(resume, job_desc)

    def full_pipeline(self, resume: dict, job_desc: str = None) -> dict:
        """Run everything at once"""
        result = self.analyze_resume(resume)
        if job_desc:
            result['ats_result'] = self.score_ats(resume, job_desc)
        return result

# Singleton instance
agent = ResumeAgent()

if __name__ == "__main__":
    test_resume = {
        "name": "Sri",
        "role": "Full Stack Developer",
        "skills": ["Python", "FastAPI", "React", "MongoDB", "Machine Learning"],
        "experience": "Fresher"
    }
    result = agent.full_pipeline(test_resume, job_desc="Python developer with REST API skills")
    print(result)