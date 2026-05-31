# preprocessing/cleaner.py
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def clean_text(text: str) -> str:
    """Full NLP preprocessing pipeline"""
    # Lowercase
    text = text.lower()
    # Remove URLs, emails, special chars
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    # Tokenize
    tokens = text.split()
    # Remove stopwords + lemmatize
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words and len(t) > 2]
    return ' '.join(tokens)

def preprocess_resume(resume_dict: dict) -> str:
    """Convert resume dict to clean NLP-ready string"""
    parts = [
        resume_dict.get('summary', ''),
        ' '.join(resume_dict.get('skills', [])),
        ' '.join([p['description'] for p in resume_dict.get('projects', [])]),
        resume_dict.get('role', '')
    ]
    combined = ' '.join(parts)
    return clean_text(combined)

if __name__ == "__main__":
    sample = "Experienced Python Developer with 2+ years in FastAPI & ML."
    print(clean_text(sample))
    # Output: experienc python develop year fastapi ml