"""
Stage 4: Local LLM & Personalized Recommendations Package.
"""
from src.stage4_recommendations.local_llm import LocalLLMClient
from src.stage4_recommendations.recommender import ResumeRecommender
from src.stage4_recommendations.report_generator import ReportGenerator

__all__ = [
    "LocalLLMClient",
    "ResumeRecommender",
    "ReportGenerator"
]

