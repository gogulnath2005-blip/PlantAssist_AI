from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class SourceResult(BaseModel):
    document_number: str
    title: str
    revision: str
    effective_date: str | None
    page: int
    section: str | None
    excerpt: str
    score: float
    revision_status: str


class AskResponse(BaseModel):
    question: str
    status: str
    answer: str
    evidence_strength: str
    sources: list[SourceResult]
    note: str | None = None
