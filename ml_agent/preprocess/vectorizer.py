# preprocessing/vectorizer.py
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer

# ── TF-IDF Vectorizer ──────────────────────────────────
class TFIDFVectorizer:
    def __init__(self, max_features=5000):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),   # unigrams + bigrams
            sublinear_tf=True
        )

    def fit_transform(self, texts):
        return self.vectorizer.fit_transform(texts)

    def transform(self, texts):
        return self.vectorizer.transform(texts)

    def save(self, path="data/models/tfidf.pkl"):
        with open(path, 'wb') as f:
            pickle.dump(self.vectorizer, f)

    def load(self, path="data/models/tfidf.pkl"):
        with open(path, 'rb') as f:
            self.vectorizer = pickle.load(f)

# ── BERT Sentence Embeddings ───────────────────────────
class BERTVectorizer:
    def __init__(self):
        # Free lightweight BERT model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def encode(self, texts):
        """Returns numpy array of shape (n, 384)"""
        return self.model.encode(texts, convert_to_numpy=True)

    def similarity(self, text1: str, text2: str) -> float:
        """Cosine similarity between two texts"""
        emb1 = self.model.encode([text1])
        emb2 = self.model.encode([text2])
        cos_sim = np.dot(emb1, emb2.T) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )
        return float(cos_sim[0][0])