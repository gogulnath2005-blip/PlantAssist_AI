from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import DOCUMENTS_DIR, INDEX_PATH
from app.schemas import AskRequest, AskResponse, SourceResult
from app.services.index_store import build_index, load_index, save_index
from app.services.retrieval import LocalRetriever

app = FastAPI(title="PlantAssist AI", version="0.1.0",
              description="Local, revision-aware retrieval over manufacturing SOP PDFs.")
# Frontend static files
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)
_index = None
_retriever = None

def refresh_index():
    global _index, _retriever
    _index = load_index(INDEX_PATH)
    _retriever = LocalRetriever(_index["chunks"])

@app.on_event("startup")
def startup():
    if INDEX_PATH.exists():
        refresh_index()

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")
def home():
    return """<html><head><title>PlantAssist AI API</title></head>
    <body style='font-family:Arial;padding:2rem'><h1>PlantAssist AI – Phase 3</h1>
    <p>Backend is running. Use <a href='/docs'>/docs</a> to explore the API.</p></body></html>"""

@app.get("/api/health")
def health():
    return {"status": "ok", "index_loaded": _index is not None,
            "documents": len(_index["documents"]) if _index else 0,
            "chunks": len(_index["chunks"]) if _index else 0}

@app.get("/api/documents")
def documents():
    if _index is None:
        return {"documents": [], "message": "Index not built. POST /api/reindex first."}
    return {"documents": _index["documents"], "ingestion_errors": _index.get("errors", [])}

@app.post("/api/reindex")
def reindex():
    try:
        new_index = build_index(DOCUMENTS_DIR)
        save_index(new_index, INDEX_PATH)
        refresh_index()
        return {"status": "indexed", "documents": len(_index["documents"]),
                "chunks": len(_index["chunks"]), "errors": _index["errors"]}
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if _retriever is None:
        raise HTTPException(status_code=503, detail="Index is not ready. Add PDFs and call POST /api/reindex.")
    matches = _retriever.search(request.question, top_k=5)
    if not matches or matches[0]["score"] < 0.15:
        return AskResponse(
            question=request.question, status="abstained",
            answer="I could not find sufficiently relevant evidence in the indexed SOP documents. Do not rely on an unsupported instruction; check the approved procedure or contact the responsible supervisor.",
            evidence_strength="none", sources=[],
            note="No answer was generated because the retrieved evidence was insufficient."
        )
    sources = [
        SourceResult(
            document_number=m["document_number"], title=m["title"],
            revision=m["revision"], effective_date=m.get("effective_date"),
            page=m["page"], section=m.get("section"), excerpt=m["text"],
            score=m["score"], revision_status=m.get("revision_status", "unknown")
        ) for m in matches
    ]
    top = matches[0]
    history_note = "Historical revision requested; verify against the current approved procedure before acting." if "historical" in request.question.lower() or "revision 03" in request.question.lower() or "rev 03" in request.question.lower() else None
    return AskResponse(
        question=request.question, status="evidence_found",
        answer="Relevant source text was found. Phase 3 returns retrieved evidence only; it does not yet generate or interpret a final operational instruction. Review the excerpt and cited document before acting.",
        evidence_strength="moderate" if top["score"] < 0.8 else "strong",
        sources=sources, note=history_note
    )
