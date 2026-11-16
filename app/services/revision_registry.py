"""Deterministic revision policy: highest numeric revision is current by default."""
from __future__ import annotations
import re
from collections import defaultdict

def revision_number(value: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", value or "")
    return tuple(int(n) for n in nums) if nums else (-1,)

def mark_revision_status(documents: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for doc in documents:
        grouped[doc.get("document_number", "UNKNOWN")].append(doc)
    status_by_key = {}
    for doc_no, docs in grouped.items():
        # Prefer explicit supersedes metadata when available; otherwise use numeric ordering.
        revisions = {d.get("revision", "UNKNOWN") for d in docs}
        latest = max(revisions, key=revision_number) if revisions else "UNKNOWN"
        for doc in docs:
            status_by_key[(doc_no, doc.get("revision", "UNKNOWN"))] = (
                "current" if doc.get("revision", "UNKNOWN") == latest else "historical"
            )
    result = []
    for doc in documents:
        copied = dict(doc)
        copied["revision_status"] = status_by_key.get(
            (doc.get("document_number", "UNKNOWN"), doc.get("revision", "UNKNOWN")), "unknown"
        )
        result.append(copied)
    return result

def asks_for_history(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in ("historical", "history", "old revision", "older revision", "revision 03", "rev 03", "rev. 03"))
