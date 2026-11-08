"""
Semantic Similarity Engine using Local Hugging Face Sentence Transformers
with Scikit-Learn TF-IDF Cosine Similarity Fallback.
Zero external API calls. Runs 100% locally on CPU.
"""
import numpy as np
from typing import Tuple, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import DEFAULT_EMBEDDING_MODEL


class SemanticSimilarityEngine:
    """Calculates semantic similarity between Resume profile and Job Description."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
        self._model_load_attempted = False
        self.engine_type = "Uninitialized"

    def _load_transformer_model(self):
        """Lazy load Hugging Face SentenceTransformer."""
        if not self._model_load_attempted:
            self._model_load_attempted = True
            try:
                from sentence_transformers import SentenceTransformer
                # Load local / cached Hugging Face model
                self._model = SentenceTransformer(self.model_name)
                self.engine_type = f"HuggingFace ({self.model_name})"
            except Exception as e:
                # Graceful fallback to TF-IDF if offline or model unavailable
                self._model = None
                self.engine_type = "TF-IDF + Cosine (Local Fallback)"

    def compute_similarity(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Compute semantic similarity score between 0.0 and 1.0.
        Returns score, engine used, and confidence.
        """
        self._load_transformer_model()

        if not resume_text.strip() or not jd_text.strip():
            return {
                "similarity_score": 0.0,
                "percentage": 0.0,
                "engine": self.engine_type,
                "confidence": "Low (Empty text)"
            }

        # 1. Hugging Face Sentence Transformers Path
        if self._model is not None:
            try:
                embeddings = self._model.encode(
                    [resume_text, jd_text],
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                sim = float(np.dot(embeddings[0], embeddings[1]))
                # Clamp between 0.0 and 1.0
                score = max(0.0, min(1.0, sim))
                return {
                    "similarity_score": round(score, 4),
                    "percentage": round(score * 100.0, 1),
                    "engine": self.engine_type,
                    "confidence": "High (Dense Neural Embeddings)"
                }
            except Exception:
                pass  # Fall through to TF-IDF

        # 2. Local TF-IDF Fallback Path
        tfidf_score = self._compute_tfidf_similarity(resume_text, jd_text)
        return {
            "similarity_score": round(tfidf_score, 4),
            "percentage": round(tfidf_score * 100.0, 1),
            "engine": "TF-IDF + Cosine Similarity (Local)",
            "confidence": "Medium (N-gram Lexical Overlap)"
        }

    def _compute_tfidf_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts using TF-IDF."""
        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True
            )
            matrix = vectorizer.fit_transform([text_a, text_b])
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            return float(max(0.0, min(1.0, sim)))
        except Exception:
            return 0.5

