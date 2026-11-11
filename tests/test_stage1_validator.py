"""
Unit tests for Stage 1: Resume Upload and Text Extraction.
"""
import pytest
from pathlib import Path
from src.stage1_ingestion.validator import ResumeValidator
from src.stage1_ingestion.extractor import PDFResumeExtractor
from src.config import SAMPLE_RESUMES_DIR


def test_validator_rejects_non_pdf():
    val = ResumeValidator.validate_bytes(b"Hello world fake text", "resume.docx")
    assert not val.is_valid
    assert any("Only PDF documents" in err or "Only PDF files" in err for err in val.errors)

    val_ppt = ResumeValidator.validate_bytes(b"Hello world fake text", "resume.pptx")
    assert not val_ppt.is_valid
    assert any("Only PDF documents" in err or "Only PDF files" in err for err in val_ppt.errors)


def test_validator_rejects_files_over_2mb():
    over_2mb = b"%PDF-1.4\n" + b"X" * (int(2.1 * 1024 * 1024))
    val = ResumeValidator.validate_bytes(over_2mb, "heavy_resume.pdf")
    assert not val.is_valid
    assert any("exceeds the maximum allowed limit of 2 MB" in err for err in val.errors)


def test_validator_rejects_empty_file():
    val = ResumeValidator.validate_bytes(b"", "empty.pdf")
    assert not val.is_valid
    assert any("too small" in err for err in val.errors)


def test_validator_detects_invalid_magic_bytes():
    fake_pdf = b"NOT_A_PDF_HEADER" + b"A" * 200
    val = ResumeValidator.validate_bytes(fake_pdf, "test.pdf")
    assert not val.is_valid
    assert any("missing %PDF-" in err for err in val.errors)


def test_extractor_extracts_sample_pdf():
    sample_pdf = SAMPLE_RESUMES_DIR / "resume_senior_fullstack.pdf"
    assert sample_pdf.exists(), "Sample PDF must exist"

    extractor = PDFResumeExtractor()
    doc = extractor.extract_from_path(sample_pdf)

    assert doc.validation.is_valid
    assert doc.validation.page_count >= 1
    assert doc.validation.character_count > 100
    assert "Alex Mercer" in doc.normalized_text
    assert "Python" in doc.normalized_text

