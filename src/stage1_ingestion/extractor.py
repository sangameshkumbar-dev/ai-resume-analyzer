"""
Dual-engine PDF text extractor with layout preservation and text normalization.
"""
import io
from pathlib import Path
from typing import Union, BinaryIO, Optional
import pdfplumber
from pypdf import PdfReader

from src.stage1_ingestion.models import ExtractedDocument, ValidationResult
from src.stage1_ingestion.validator import ResumeValidator
from src.utils.text_helpers import normalize_text


class PDFResumeExtractor:
    """Extracts raw text from PDF files using pdfplumber with pypdf fallback."""

    def __init__(self, validator: Optional[ResumeValidator] = None):
        self.validator = validator or ResumeValidator()

    def extract_from_bytes(self, file_bytes: bytes, filename: str = "uploaded_resume.pdf") -> ExtractedDocument:
        """Validate and extract text from in-memory byte buffer."""
        validation = self.validator.validate_bytes(file_bytes, filename)
        if not validation.is_valid:
            return ExtractedDocument(
                filename=filename,
                raw_text="",
                normalized_text="",
                pages_text=[],
                metadata={},
                validation=validation
            )

        pages_text = []
        metadata = {}

        # 1. Primary Engine: pdfplumber (Preserves layout, extracts columns and tables cleanly)
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                metadata = pdf.metadata or {}
                for page in pdf.pages:
                    # layout=True preserves visual columns and spaces
                    page_text = page.extract_text(layout=False, x_tolerance=2, y_tolerance=2)
                    pages_text.append(page_text or "")
        except Exception:
            # 2. Fallback Engine: pypdf
            pages_text = []
            try:
                reader = PdfReader(io.BytesIO(file_bytes), strict=False)
                metadata = reader.metadata or {}
                for page in reader.pages:
                    pages_text.append(page.extract_text() or "")
            except Exception as e:
                validation.errors.append(f"Extraction failed across both engines: {str(e)}")
                validation.is_valid = False

        raw_combined = "\n\n--- PAGE BREAK ---\n\n".join(pages_text)
        normalized = normalize_text("\n\n".join(pages_text))

        # Update character and word counts in validation result after full extraction
        validation.character_count = len(normalized)
        validation.word_count = len(normalized.split())

        return ExtractedDocument(
            filename=filename,
            raw_text=raw_combined,
            normalized_text=normalized,
            pages_text=pages_text,
            metadata=dict(metadata),
            validation=validation
        )

    def extract_from_path(self, file_path: Union[str, Path]) -> ExtractedDocument:
        """Extract text from local file path."""
        path = Path(file_path)
        with open(path, "rb") as f:
            content = f.read()
        return self.extract_from_bytes(content, filename=path.name)

