# PlantAssist AI — Phase 3 backend

Phase 3 implements local PDF ingestion, metadata extraction, page-aware chunking, a persistent JSON index, revision status, lexical retrieval and basic FastAPI endpoints.

> Important: this phase is a retrieval backend, not a complete AI answer generator. `/api/ask` returns source evidence and explicitly says it has not interpreted it into operating instructions. Evidence-grounded answer generation and stricter safety validation are later phases.

## Windows setup (PowerShell)

```powershell
cd plantassist-ai
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again.

Copy the four assignment PDFs into `documents/`. Do not commit them publicly unless sharing is permitted.

Build the index:
```powershell
python -m uvicorn app.main:app --reload
```
Open a second PowerShell terminal (activate `.venv` there too), then:
```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/reindex
```

Open `http://127.0.0.1:8000/docs`. Test:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/documents
```

## Git Bash
```bash
cd plantassist-ai
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
In another terminal:
```bash
curl -X POST http://127.0.0.1:8000/api/reindex
curl http://127.0.0.1:8000/api/health
```

## API

- `GET /api/health` — process and index status.
- `GET /api/documents` — extracted document metadata and ingestion errors.
- `POST /api/reindex` — rebuild local index from `documents/*.pdf`.
- `POST /api/ask` — lexical retrieval with source metadata and excerpts.

Example request body:
```json
{"question":"What is the normal hydraulic pressure range for the TX-200?"}
```

## Retrieval and revision policy

Text is extracted page by page with `pypdf`. Chunks retain the 1-based page number, detected section, document number, title, revision and effective date. A local BM25-style scorer ranks matching chunks. For each document number, the numerically highest revision is marked current; lower revisions are historical. Default retrieval excludes historical chunks. A question explicitly mentioning historical/older revision language searches historical chunks only.

This is a deterministic first implementation. It does not yet understand every possible document-control convention. Before production, use an explicit approved-revision registry or document-control metadata instead of assuming the highest revision is always approved/current.

## Tests

```powershell
python -m pytest -q
```
The tests include metadata detection, page numbering, chunking, revision status, retrieval filtering and API validation. They use small isolated fixtures/mocks; run a real ingestion against the four supplied PDFs as a separate acceptance check.

## Known limitations

- Scanned/image-only PDFs need OCR; pypdf extracts embedded text only.
- Metadata detection uses regular expressions and may need tuning for different templates.
- Numeric revision ordering is a fallback, not a substitute for formal document control.
- Retrieval is lexical; synonyms and semantic matching are limited.
- Phase 3 does not produce an operational answer or authorize a machine action.
- The index is local JSON and should be rebuilt after changing source PDFs.
