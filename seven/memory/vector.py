"""
Lightweight local semantic memory without heavy ML deps.
Hashing / bag-of-words cosine over stored embeddings table.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import List, Optional, Tuple

from seven.memory.store import Memory

_DIM = 256
_TOKEN = re.compile(r"[a-z0-9_]{2,}", re.I)


def embed_text(text: str, dim: int = _DIM) -> List[float]:
    """Deterministic feature hashing embedding."""
    vec = [0.0] * dim
    tokens = _TOKEN.findall((text or "").lower())
    if not tokens:
        return vec
    for t in tokens:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) & 1 else -1.0
        vec[idx] += sign
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: List[float], b: List[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(a[i] * b[i] for i in range(n))


class SemanticMemory:
    def __init__(self, memory: Memory):
        self.memory = memory

    def index(self, text: str, ref_type: str = "note", ref_id: Optional[int] = None) -> int:
        text = (text or "").strip()
        if not text:
            return -1
        vec = embed_text(text)
        return self.memory.add_embedding(ref_type, ref_id, text[:2000], vec)

    def index_message(self, role: str, content: str) -> int:
        return self.index(f"{role}: {content}", ref_type="message")

    def search(self, query: str, limit: int = 6) -> List[Tuple[float, dict]]:
        qv = embed_text(query)
        scored = []
        for row in self.memory.all_embeddings(800):
            score = cosine(qv, row.get("vector") or [])
            if score > 0.05:
                scored.append((score, row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:limit]

    def search_text(self, query: str, limit: int = 6) -> str:
        hits = self.search(query, limit=limit)
        if not hits:
            # fallback lexical
            facts = self.memory.search_facts(query, limit=limit)
            if not facts:
                return f"No semantic/lexical hits for: {query}"
            return "Lexical facts:\n" + "\n".join(
                f"- {f.get('key') or ''}: {f['value']}" for f in facts
            )
        lines = [f"Semantic hits for: {query}"]
        for score, row in hits:
            lines.append(f"- ({score:.2f}) [{row.get('ref_type')}] {row.get('text')[:200]}")
        return "\n".join(lines)
