"""Persistent JSON index and PDF directory ingestion."""
from __future__ import annotations
import json
from pathlib import Path
from .pdf_ingestion import extract_pdf
from .revision_registry import mark_revision_status

def build_index(documents_dir: Path) -> dict:
    pdf_paths = sorted(documents_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(
            f"No PDF files found in {documents_dir}. Copy the four assignment PDFs into the documents folder."
        )
    document_metadata = []
    all_chunks = []
    errors = []
    for pdf_path in pdf_paths:
        try:
            extracted = extract_pdf(pdf_path)
            document_metadata.append(extracted["metadata"])
            all_chunks.extend(extracted["chunks"])
        except Exception as exc:
            errors.append({"filename": pdf_path.name, "error": str(exc)})
    if not document_metadata:
        raise RuntimeError(f"Could not extract any PDFs. Errors: {errors}")
    document_metadata = mark_revision_status(document_metadata)
    status_map = {(d["document_number"], d["revision"]): d["revision_status"] for d in document_metadata}
    for chunk in all_chunks:
        chunk["revision_status"] = status_map.get((chunk["document_number"], chunk["revision"]), "unknown")
    return {
        "documents": document_metadata,
        "chunks": all_chunks,
        "errors": errors,
        "chunk_count": len(all_chunks),
    }

def save_index(index: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

def load_index(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
