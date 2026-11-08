"""
File type, size, security, and text extractability validator for resumes.
"""
import io
from pathlib import Path
from typing import Union, BinaryIO
from pypdf import PdfReader

from src.config import (
    MAX_FILE_SIZE_BYTES,
    MIN_FILE_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
    MIN_EXTRACTED_CHAR_COUNT,
)
from src.stage1_ingestion.models import ValidationResult


class ResumeValidator:
    """Validates uploaded resume files for type, size, corruption, encryption, and usable text."""

    @staticmethod
    def validate_bytes(file_bytes: bytes, filename: str) -> ValidationResult:
        """Validate in-memory bytes (typical for Streamlit or web upload)."""
        file_size = len(file_bytes)
        errors = []
        warnings = []
        is_valid = True
        page_count = 0
        char_count = 0
        word_count = 0
        is_encrypted = False
        is_scanned_suspicion = False

        # 1. Filename extension check
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"Invalid file extension '{ext}'. Only PDF files are supported.")
            is_valid = False

        # 2. File size checks
        if file_size < MIN_FILE_SIZE_BYTES:
            errors.append(f"File size ({file_size} bytes) is too small to be a valid resume.")
            is_valid = False
        elif file_size > MAX_FILE_SIZE_BYTES:
            errors.append(
                f"File size ({round(file_size / (1024*1024), 2)} MB) exceeds the maximum allowed limit of "
                f"{MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
            )
            is_valid = False

        # 3. PDF Magic Byte check (%PDF-)
        if not file_bytes.startswith(b"%PDF-"):
            errors.append("File header does not match PDF specification (missing %PDF- signature).")
            is_valid = False

        # If fatal format errors already exist, return early
        if not is_valid:
            return ValidationResult(
                is_valid=False,
                filename=filename,
                file_size_bytes=file_size,
                errors=errors,
                warnings=warnings
            )

        # 4. Deep PDF Structure & Extractability Inspection
        try:
            stream = io.BytesIO(file_bytes)
            reader = PdfReader(stream)
            page_count = len(reader.pages)

            if reader.is_encrypted:
                is_encrypted = True
                errors.append("The PDF document is password-protected or encrypted. Please remove encryption.")
                is_valid = False
                return ValidationResult(
                    is_valid=False,
                    filename=filename,
                    file_size_bytes=file_size,
                    page_count=page_count,
                    is_encrypted=True,
                    errors=errors,
                    warnings=warnings
                )

            if page_count == 0:
                errors.append("PDF contains 0 pages.")
                is_valid = False
                return ValidationResult(
                    is_valid=False,
                    filename=filename,
                    file_size_bytes=file_size,
                    page_count=0,
                    errors=errors,
                    warnings=warnings
                )

            # Sample text extraction to test extractability
            all_text = ""
            for idx, page in enumerate(reader.pages):
                try:
                    p_text = page.extract_text() or ""
                    all_text += " " + p_text
                except Exception as ex:
                    warnings.append(f"Could not extract text from page {idx+1}: {str(ex)}")

            char_count = len(all_text.strip())
            word_count = len(all_text.split())

            # Usable text validation
            if char_count < MIN_EXTRACTED_CHAR_COUNT:
                is_scanned_suspicion = True
                warnings.append(
                    f"Extracted only {char_count} characters. This PDF might be an image/scanned document "
                    f"without an embedded OCR text layer."
                )

            # Page count warnings for corporate resumes
            if page_count > 6:
                warnings.append(f"Resume is {page_count} pages long. Industry standard resumes are typically 1-3 pages.")

        except Exception as e:
            errors.append(f"Failed to parse PDF document structure: {str(e)}")
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            filename=filename,
            file_size_bytes=file_size,
            page_count=page_count,
            character_count=char_count,
            word_count=word_count,
            is_encrypted=is_encrypted,
            is_scanned_suspicion=is_scanned_suspicion,
            errors=errors,
            warnings=warnings
        )

    @classmethod
    def validate_file_path(cls, file_path: Union[str, Path]) -> ValidationResult:
        """Validate a resume directly from a filesystem path."""
        path = Path(file_path)
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                filename=path.name,
                file_size_bytes=0,
                errors=[f"File '{file_path}' does not exist."]
            )
        with open(path, "rb") as f:
            content = f.read()
        return cls.validate_bytes(content, path.name)

