"""
Data models and schemas for Stage 1: Ingestion and Validation.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ValidationResult:
    """Represents the outcome of resume validation checks."""
    is_valid: bool
    filename: str
    file_size_bytes: int
    page_count: int = 0
    character_count: int = 0
    word_count: int = 0
    is_encrypted: bool = False
    is_scanned_suspicion: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def file_size_kb(self) -> float:
        return round(self.file_size_bytes / 1024.0, 2)

    @property
    def quality_badge(self) -> str:
        if not self.is_valid:
            return "❌ Invalid"
        if self.is_scanned_suspicion:
            return "⚠️ Low Text Density (Possible Scanned Doc)"
        if self.warnings:
            return "🟡 Good (Minor Warnings)"
        return "🟢 High Quality Text"


@dataclass
class ExtractedDocument:
    """Contains raw and normalized text extracted from the resume alongside metadata."""
    filename: str
    raw_text: str
    normalized_text: str
    pages_text: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation: Optional[ValidationResult] = None

