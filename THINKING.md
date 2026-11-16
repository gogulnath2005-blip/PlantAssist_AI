# Engineering notes — PlantAssist AI

## Phase 3 implementation decisions

- I separated PDF extraction, revision classification, indexing and retrieval so each can be tested independently.
- Every extracted chunk keeps its source document number, revision, effective date, page number and section label where detected.
- The retriever uses a small BM25-style lexical ranking implementation to avoid a paid API key or external service in the first working version.
- Historical revisions are excluded by default. Explicit historical queries can search historical chunks.
- The system returns source excerpts rather than pretending retrieval alone is a verified operational answer.

## Limitations to validate

- Highest numeric revision is only a fallback heuristic. Confirm the plant's document-control rule before production use.
- PDF templates vary; inspect `/api/documents` and ingestion errors after indexing.
- Scanned PDFs require OCR, which is not included in this phase.

## Personal reflection

Add your own real observations after running and testing the project. Do not claim tests, user research or deployment that you have not performed.
