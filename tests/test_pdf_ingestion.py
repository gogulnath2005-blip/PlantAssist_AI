from pathlib import Path
from unittest.mock import patch
from app.services.pdf_ingestion import detect_metadata, extract_pdf, split_into_chunks

def test_metadata_extracts_doc_number_revision_and_date():
    text = "QC-SOP-014 Incoming Material Inspection\nRevision 04\nEffective Date: 01-Jul-2026"
    data = detect_metadata(text, "incoming.pdf")
    assert data["document_number"] == "QC-SOP-014"
    assert data["revision"] == "04"
    assert data["effective_date"] == "01-Jul-2026"

def test_chunking_preserves_content_and_respects_page_text():
    chunks = split_into_chunks("1. PURPOSE\n" + ("Inspection material details. " * 80), max_chars=250, overlap=30)
    assert len(chunks) > 1
    assert all(c["text"] for c in chunks)
    assert "1. PURPOSE" in chunks[0]["text"]

def test_pdf_extraction_keeps_one_based_page_numbers(tmp_path):
    class FakePage:
        def __init__(self, text): self.text = text
        def extract_text(self): return self.text
    class FakeReader:
        def __init__(self, _): self.pages = [FakePage("SAF-SOP-003 LOTO Procedure\\nRevision 05"), FakePage("Section 4\\nApply personal lock")]
    with patch("app.services.pdf_ingestion.PdfReader", FakeReader):
        result = extract_pdf(tmp_path / "sample.pdf")
    assert [p["page"] for p in result["pages"]] == [1, 2]
    assert result["chunks"][1]["page"] == 2
