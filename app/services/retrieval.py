"""Local BM25-style retrieval with a lexical relevance gate.

The relevance gate prevents generic word overlap (for example, "plant") from
making an unrelated SOP look like evidence for a question.
This is a conservative lexical check, not semantic understanding.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .revision_registry import asks_for_history

TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-.][a-z0-9]+)*", re.I)

# Words that usually do not identify the actual subject of a procedure question.
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "how", "i", "in", "is", "it", "me", "of", "on", "or",
    "should", "the", "their", "this", "to", "was", "we", "what", "when",
    "where", "which", "who", "why", "with", "would", "according", "please",
    "current", "latest", "approved", "procedure", "document", "sop",
    "manual", "revision", "rev", "version", "plant", "hosur","point",
}

def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())

def content_terms(text: str) -> set[str]:
    """Return terms that carry subject meaning rather than generic grammar."""
    return {term for term in tokenize(text) if term not in STOP_WORDS}

class LocalRetriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.tokens = [tokenize(c.get("text", "")) for c in chunks]
        self.avgdl = sum(map(len, self.tokens)) / max(len(self.tokens), 1)
        self.df = Counter()
        for terms in self.tokens:
            self.df.update(set(terms))

    def search(self, question: str, top_k: int = 5) -> list[dict]:
        query_terms = set(tokenize(question))
        meaningful_terms = content_terms(question)
        if not query_terms or not meaningful_terms or not self.chunks:
            return []

        history = asks_for_history(question)
        scored = []
        n = len(self.chunks)

        for chunk, terms in zip(self.chunks, self.tokens):
            status = chunk.get("revision_status", "unknown")
            if history and status != "historical":
                continue
            if not history and status == "historical":
                continue

            # Relevance gate: require at least one subject-specific query term
            # to occur in the candidate passage. Generic words such as "plant"
            # and "where" cannot make an unrelated document relevant.
            matched_terms = meaningful_terms.intersection(terms)
            coverage = len(matched_terms) / len(meaningful_terms)
            if not matched_terms or coverage < 0.20:
                continue

            counts = Counter(terms)
            score = 0.0
            for term in query_terms:
                tf = counts[term]
                if not tf:
                    continue
                idf = math.log(1 + (n - self.df[term] + 0.5) / (self.df[term] + 0.5))
                denominator = tf + 1.5 * (
                    1 - 0.75 + 0.75 * len(terms) / max(self.avgdl, 1)
                )
                score += idf * (tf * 2.5) / denominator

            if score > 0:
                item = dict(chunk)
                item["score"] = round(score, 4)
                item["matched_terms"] = sorted(matched_terms)
                item["query_coverage"] = round(coverage, 3)
                scored.append(item)

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]
