# models/skill_extractor.py
"""
Model: TF-IDF + Logistic Regression → upgraded to LSTM
Task: Given resume text → predict job role + extract skills
Dataset: Kaggle Resume Dataset (2484 resumes, 25 categories)
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from preprocessing.cleaner import clean_text
from preprocessing.vectorizer import TFIDFVectorizer

# ── Step 1: Load & Clean Data ──────────────────────────
def load_data(path="data/raw/resume_dataset.csv"):
    df = pd.read_csv(path)
    df = df[['Resume', 'Category']].dropna()
    df['clean_resume'] = df['Resume'].apply(clean_text)
    print(f"Loaded {len(df)} resumes across {df['Category'].nunique()} categories")
    return df

# ── Step 2: Train Model ────────────────────────────────
def train_classifier(df):
    vectorizer = TFIDFVectorizer(max_features=5000)
    X = vectorizer.fit_transform(df['clean_resume'])
    y = df['Category']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver='lbfgs',
        multi_class='multinomial'
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    print(f"Accuracy: {model.score(X_test, y_test):.4f}")

    return model, vectorizer

# ── Step 3: Extract Skills ─────────────────────────────
KNOWN_SKILLS = [
    "python", "java", "react", "node", "fastapi", "mongodb",
    "sql", "docker", "kubernetes", "tensorflow", "pytorch",
    "nlp", "machine learning", "deep learning", "aws", "git"
]

def extract_skills(text: str) -> list:
    text_lower = text.lower()
    return [skill for skill in KNOWN_SKILLS if skill in text_lower]

# ── Step 4: Predict Role ───────────────────────────────
def predict_role(text: str, model, vectorizer) -> dict:
    clean = clean_text(text)
    vec = vectorizer.transform([clean])
    role = model.predict(vec)[0]
    proba = model.predict_proba(vec)[0]
    confidence = round(max(proba) * 100, 2)
    skills = extract_skills(text)
    return {
        "predicted_role": role,
        "confidence": confidence,
        "extracted_skills": skills
    }

# ── Step 5: Save Model ─────────────────────────────────
def save_model(model, vectorizer):
    with open("data/models/skill_extractor.pkl", 'wb') as f:
        pickle.dump(model, f)
    vectorizer.save("data/models/tfidf.pkl")
    print("Model saved!")

if __name__ == "__main__":
    df = load_data()
    model, vectorizer = train_classifier(df)
    save_model(model, vectorizer)
    # Test prediction
    sample = "Python developer with experience in FastAPI, MongoDB, React and ML"
    print(predict_role(sample, model, vectorizer))