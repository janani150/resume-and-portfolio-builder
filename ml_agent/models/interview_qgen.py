# models/interview_qgen.py
"""
Hybrid approach: Rule-based templates + TF-IDF skill matching
No heavy model needed — smart logic gives great results
"""
from preprocessing.cleaner import extract_skills

QUESTION_TEMPLATES = {
    "python": [
        "Explain the difference between list and tuple in Python.",
        "What are Python decorators? Give an example.",
        "How does Python's GIL work?",
    ],
    "react": [
        "Explain the virtual DOM and how React uses it.",
        "What is the difference between useState and useReducer?",
        "How do you optimize a React app for performance?",
    ],
    "machine learning": [
        "Explain overfitting and how to prevent it.",
        "What is the bias-variance tradeoff?",
        "Compare supervised vs unsupervised learning.",
    ],
    "fastapi": [
        "How does FastAPI handle async requests?",
        "Explain dependency injection in FastAPI.",
        "How do you implement JWT auth in FastAPI?",
    ],
}

BEHAVIORAL = [
    "Tell me about a challenging project you worked on.",
    "How do you handle tight deadlines?",
    "Describe a time you debugged a critical issue.",
]

DSA = [
    "Explain time complexity of Quick Sort vs Merge Sort.",
    "How would you detect a cycle in a linked list?",
    "What is dynamic programming? Give an example.",
]

def generate_questions(skills: list, role: str) -> dict:
    questions = {"technical": [], "dsa": DSA[:3], "behavioral": BEHAVIORAL[:2]}

    for skill in skills:
        skill_lower = skill.lower()
        for key, qs in QUESTION_TEMPLATES.items():
            if key in skill_lower:
                questions["technical"].extend(qs[:2])

    if not questions["technical"]:
        questions["technical"] = [
            f"Explain your experience with {skill}." for skill in skills[:3]
        ]

    return questions