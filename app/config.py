from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
DATA_DIR = PROJECT_ROOT / "data"
INDEX_PATH = DATA_DIR / "document_index.json"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
