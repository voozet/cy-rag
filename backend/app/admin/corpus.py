"""Corpus document CRUD, operating directly on backend/data/raw/*.md.

Every write (create/update/delete) is followed by the caller triggering
store.build() to keep the FAISS index in sync -- see app/admin/router.py.
"""
from ..config import RAW_DIR
from ..rag.chunker import chunk_text
from ..rag.frontmatter import parse_frontmatter, serialize_document
from ..schemas import CorpusDocument, CorpusDocumentCreate, CorpusDocumentUpdate


def _path(slug: str):
    return RAW_DIR / f"{slug}.md"


def _read(slug: str) -> CorpusDocument | None:
    path = _path(slug)
    if not path.exists():
        return None
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return CorpusDocument(
        slug=slug,
        title=meta.get("title", slug),
        source=meta.get("source", "Unknown"),
        url=meta.get("url", ""),
        section=meta.get("section", ""),
        text=body,
        word_count=len(body.split()),
        chunks=len(chunk_text(body)),
    )


def list_documents() -> list[CorpusDocument]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    docs = [_read(p.stem) for p in sorted(RAW_DIR.glob("*.md"))]
    return [d for d in docs if d is not None]


def get_document(slug: str) -> CorpusDocument | None:
    return _read(slug)


def create_document(payload: CorpusDocumentCreate) -> CorpusDocument:
    path = _path(payload.slug)
    if path.exists():
        raise FileExistsError(f"A document with slug '{payload.slug}' already exists")
    meta = {"title": payload.title, "source": payload.source, "url": payload.url, "section": payload.section}
    path.write_text(serialize_document(meta, payload.text), encoding="utf-8")
    return _read(payload.slug)


def update_document(slug: str, payload: CorpusDocumentUpdate) -> CorpusDocument:
    path = _path(slug)
    if not path.exists():
        raise FileNotFoundError(f"No document with slug '{slug}'")
    meta = {"title": payload.title, "source": payload.source, "url": payload.url, "section": payload.section}
    path.write_text(serialize_document(meta, payload.text), encoding="utf-8")
    return _read(slug)


def delete_document(slug: str) -> None:
    path = _path(slug)
    if not path.exists():
        raise FileNotFoundError(f"No document with slug '{slug}'")
    path.unlink()


def document_count() -> int:
    return len(list(RAW_DIR.glob("*.md")))
