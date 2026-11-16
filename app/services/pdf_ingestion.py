"""PDF text extraction, metadata detection and page-aware chunking."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

DOC_NO_RE = re.compile(r"\b([A-Z]{2,5}-(?:SOP|MAN)-[A-Z0-9-]+)\b", re.I)
REV_RE = re.compile(r"\b(?:Revision|Rev\.?)\s*[:\-]?\s*([A-Z0-9.]+)\b", re.I)
DATE_RE = re.compile(
    r"\b(?:Effective\s+Date|Effective)\s*[:\-]?\s*"
    r"(\d{1,2}[-/ ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/ ]\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4})",
    re.I,
)
TITLE_RE = re.compile(r"(?im)^\s*(?:title\s*:\s*)?(.{5,100}(?:procedure|inspection|maintenance|manual|tagout).*)$")

def _first(pattern: re.Pattern, text: str, default: str = "") -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else default

def detect_metadata(text: str, filename: str) -> dict[str, Any]:
    """Read metadata from document text; filename is only a fallback for document number."""
    doc_no = _first(DOC_NO_RE, text)
    if not doc_no:
        doc_no = _first(DOC_NO_RE, filename.replace("_", "-"))
    revision = _first(REV_RE, text, "UNKNOWN")
    effective_date = _first(DATE_RE, text) or None
    title = _first(TITLE_RE, text)
    if not title:
        # Use a readable first non-empty line, but do not invent a title.
        title = next((line.strip() for line in text.splitlines() if len(line.strip()) >= 5), Path(filename).stem)
    supersedes_match = re.search(r"\b(?:supersedes|superseded)\s+(?:by\s+)?(?:Revision|Rev\.?)\s*([A-Z0-9.]+)", text, re.I)
    supersedes = supersedes_match.group(1) if supersedes_match else None
    return {
        "document_number": doc_no or "UNKNOWN",
        "title": title[:140],
        "revision": revision,
        "effective_date": effective_date,
        "supersedes_revision": supersedes,
        "filename": filename,
    }

def split_into_chunks(text: str, max_chars: int = 900, overlap: int = 150) -> list[dict[str, str]]:
    """Split extracted page text while trying to retain nearby section headings."""
    cleaned = re.sub(r"[ \t]+", " ", text).strip()
    if not cleaned:
        return []
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    section = None
    chunks: list[dict[str, str]] = []
    current = ""
    current_section = None

    def looks_like_heading(line: str) -> bool:
        return bool(re.match(r"^(?:\d+(?:\.\d+)*[\s.)-]+|section\s+\d+|[A-Z][A-Z0-9 /&()-]{4,})", line, re.I))

    for line in lines:
        if looks_like_heading(line):
            section = line[:120]
        if current and len(current) + len(line) + 1 > max_chars:
            chunks.append({"text": current.strip(), "section": current_section or section or ""})
            carry = current[-overlap:] if overlap else ""
            current = (carry + "\n" + line).strip()
            current_section = section
        else:
            current = (current + "\n" + line).strip()
            current_section = current_section or section
    if current:
        chunks.append({"text": current.strip(), "section": current_section or section or ""})
    return chunks

def extract_pdf(path: Path) -> dict[str, Any]:
    """Extract each page separately and retain 1-based PDF page numbers."""
    reader = PdfReader(str(path))
    page_records = []
    all_text = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_records.append({"page": page_number, "text": page_text})
        all_text.append(page_text)
    combined = "\n".join(all_text)
    metadata = detect_metadata(combined, path.name)
    chunks = []
    for page_record in page_records:
        for chunk in split_into_chunks(page_record["text"]):
            chunks.append({
                **metadata,
                "page": page_record["page"],
                "section": chunk["section"] or None,
                "text": chunk["text"],
            })
    return {"metadata": metadata, "pages": page_records, "chunks": chunks}
