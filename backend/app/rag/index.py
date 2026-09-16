import hashlib
import json
import re
import threading

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .chunker import chunk_text
from .frontmatter import parse_frontmatter
from .models import Evidence
from ..config import INDEX_DIR, RAW_DIR, settings


def _vector_id(chunk_id: str) -> int:
    """Deterministic positive int64 FAISS id for a chunk id string (e.g.
    'nist-incident-response-3'). Deterministic so re-adding the same chunk
    after a rebuild always lands on the same id, and so we never need an
    external id-counter to persist alongside the index."""
    digest = hashlib.sha1(chunk_id.encode("utf-8")).digest()[:8]
    return int.from_bytes(digest, "big") & 0x7FFFFFFFFFFFFFFF


class VectorStore:
    """FAISS-backed store supporting both a full rebuild (`rebuild_all`,
    used by scripts/ingest.py and the manual 'reindex' button) and
    incremental single-document operations (`add_document`,
    `update_document`, `remove_document`, used by the admin panel) that
    only touch the vectors for the document that actually changed."""

    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)
        self.index: faiss.IndexIDMap | None = None
        self.records: dict[int, dict] = {}  # vector_id -> record (includes "slug")
        self.dim: int | None = None
        self._lock = threading.Lock()
        self._load_or_build()

    # ---------- persistence ----------
    def _index_path(self):
        return INDEX_DIR / "cyber.index"

    def _meta_path(self):
        return INDEX_DIR / "metadata.json"

    def _load_or_build(self):
        if self._index_path().exists() and self._meta_path().exists():
            self.index = faiss.read_index(str(self._index_path()))
            rows = json.loads(self._meta_path().read_text(encoding="utf-8"))
            self.records = {row["vector_id"]: row for row in rows}
            self.dim = self.index.d
            return
        self.rebuild_all()

    def _persist(self):
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self._index_path()))
        self._meta_path().write_text(
            json.dumps(list(self.records.values()), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _embed(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(embeddings, dtype="float32")

    def _chunk_records(self, slug: str) -> list[dict]:
        """Read one document from disk and turn it into chunk records
        (embeddings not computed here -- caller embeds in a single batch)."""
        path = RAW_DIR / f"{slug}.md"
        if not path.exists():
            return []
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        records = []
        for i, chunk in enumerate(chunk_text(body)):
            chunk_id = f"{slug}-{i}"
            records.append({
                "id": chunk_id,
                "vector_id": _vector_id(chunk_id),
                "slug": slug,
                "title": meta.get("title", slug),
                "source": meta.get("source", "Unknown"),
                "url": meta.get("url", ""),
                "section": meta.get("section", ""),
                "text": chunk,
            })
        return records

    # ---------- full rebuild: scripts/ingest.py, the manual "reindex" button,
    # or first startup with no saved index yet ----------
    def rebuild_all(self) -> int:
        with self._lock:
            all_records = []
            for path in sorted(RAW_DIR.glob("*.md")):
                all_records.extend(self._chunk_records(path.stem))
            if not all_records:
                raise RuntimeError(f"No markdown documents found in {RAW_DIR}")
            embeddings = self._embed([r["text"] for r in all_records])
            self.dim = embeddings.shape[1]
            index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
            ids = np.array([r["vector_id"] for r in all_records], dtype="int64")
            index.add_with_ids(embeddings, ids)
            self.index = index
            self.records = {r["vector_id"]: r for r in all_records}
            self._persist()
            return len(all_records)

    # ---------- incremental single-document operations (admin panel) ----------
    def _drop_slug(self, slug: str):
        stale_ids = [vid for vid, r in self.records.items() if r["slug"] == slug]
        if stale_ids and self.index is not None:
            self.index.remove_ids(np.array(stale_ids, dtype="int64"))
        for vid in stale_ids:
            self.records.pop(vid, None)

    def add_document(self, slug: str) -> int:
        """Embed and splice in only this document's chunks -- every other
        document's vectors are untouched. Also used for edits: drops any
        stale vectors for the slug first, so a shorter/edited document
        doesn't leave orphaned old chunks behind."""
        with self._lock:
            self._drop_slug(slug)
            records = self._chunk_records(slug)
            if records:
                embeddings = self._embed([r["text"] for r in records])
                if self.index is None:
                    self.dim = embeddings.shape[1]
                    self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
                ids = np.array([r["vector_id"] for r in records], dtype="int64")
                self.index.add_with_ids(embeddings, ids)
                for r in records:
                    self.records[r["vector_id"]] = r
            self._persist()
            return len(records)

    def update_document(self, slug: str) -> int:
        return self.add_document(slug)  # add_document already drops the old vectors first

    def remove_document(self, slug: str) -> int:
        with self._lock:
            self._drop_slug(slug)
            self._persist()
            return len(self.records)

    # kept as an alias so any external caller expecting the old full-rebuild
    # `build()` name still works
    build = rebuild_all

    # ---------- search ----------
    def search(self, query: str, k: int | None = None) -> list[Evidence]:
        """Retrieve evidence with semantic search plus a lightweight lexical signal.

        Semantic similarity is excellent for paraphrases, but short questions such as
        "What does Post-Incident Activity emphasize?" can be unfairly penalized because
        the important term is a phrase from the source. We therefore use FAISS to get
        candidates and then add a token/phrase overlap score. This keeps retrieval
        evidence-first while making exact terminology reliably retrievable.
        """
        k = k or settings.candidate_k
        if self.index is None or not self.records:
            return []

        q = self._embed([query])
        candidate_count = min(max(k, settings.top_k) * 3, len(self.records))
        scores, ids = self.index.search(q, candidate_count)

        query_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
        # Keep useful words in non-Latin queries too, while ignoring punctuation.
        query_terms = set(re.findall(r"\w+", query.lower(), flags=re.UNICODE))

        candidates = []
        for semantic, vid in zip(scores[0], ids[0]):
            if vid < 0:
                continue
            r = self.records.get(int(vid))
            if r is None:
                continue

            haystack = f"{r['title']} {r.get('section', '')} {r['text']}".lower()
            doc_terms = set(re.findall(r"\w+", haystack, flags=re.UNICODE))
            overlap = len(query_terms & doc_terms) / max(1, len(query_terms))

            # Exact multi-word phrases get a strong boost. This is particularly
            # important for named NIST/ATT&CK phases and techniques.
            normalized_query = " ".join(query.lower().split())
            phrase_boost = 0.0
            for phrase in re.findall(r"[A-Za-z][A-Za-z -]{3,}", query):
                phrase = " ".join(phrase.lower().split())
                if len(phrase) >= 6 and phrase in haystack:
                    phrase_boost = max(phrase_boost, 0.20)

            combined = float(semantic) + min(0.20, overlap * 0.20) + phrase_boost
            candidates.append((combined, float(semantic), r))

        candidates.sort(key=lambda x: x[0], reverse=True)

        results = []
        for combined, semantic, r in candidates:
            # Accept a document when either semantic retrieval is above the normal
            # threshold or lexical/phrase evidence makes the match unambiguous.
            lexical_match = combined > settings.similarity_threshold and semantic < settings.similarity_threshold
            if semantic < settings.similarity_threshold and not lexical_match:
                continue
            results.append(Evidence(
                id=r["id"], title=r["title"], source=r["source"], url=r["url"],
                section=r["section"], text=r["text"], score=combined
            ))
            if len(results) >= settings.top_k:
                break
        return results


store = VectorStore()
