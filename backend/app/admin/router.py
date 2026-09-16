from fastapi import APIRouter, Depends, Header, HTTPException

from . import corpus
from ..config import settings
from ..rag.index import store
from ..schemas import CorpusDocument, CorpusDocumentCreate, CorpusDocumentUpdate, ReindexResult


def require_admin(x_admin_token: str | None = Header(default=None)):
    """Gate for document CRUD/reindex only -- evaluation endpoints are
    public regardless (see app/main.py), since anyone viewing the deployed
    site should be able to see/re-run evaluation without a secret.

    If ADMIN_TOKEN isn't configured at all, the corpus-editing API is simply
    open (no token to check against) rather than locked out entirely --
    treat "unset" as "no protection configured", not "disabled"."""
    if not settings.admin_token:
        return
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _stats() -> ReindexResult:
    return ReindexResult(reindexed=True, chunks=len(store.records), documents=corpus.document_count())


@router.get("/documents", response_model=list[CorpusDocument])
def list_documents():
    return corpus.list_documents()


@router.get("/documents/{slug}", response_model=CorpusDocument)
def get_document(slug: str):
    doc = corpus.get_document(slug)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"No document with slug '{slug}'")
    return doc


@router.post("/documents", response_model=CorpusDocument, status_code=201)
def create_document(payload: CorpusDocumentCreate):
    try:
        doc = corpus.create_document(payload)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    # Incremental: embed and add only this document's chunks. Every other
    # document's vectors are untouched -- no full rebuild.
    store.add_document(payload.slug)
    return doc


@router.put("/documents/{slug}", response_model=CorpusDocument)
def update_document(slug: str, payload: CorpusDocumentUpdate):
    try:
        doc = corpus.update_document(slug, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    # Incremental: drops this slug's old vectors and re-embeds just its new
    # chunks. Other documents are never re-embedded or re-added.
    store.update_document(slug)
    return doc


@router.delete("/documents/{slug}", status_code=200, response_model=ReindexResult)
def delete_document(slug: str):
    if corpus.document_count() <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last document -- the corpus would be empty")
    try:
        corpus.delete_document(slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    store.remove_document(slug)
    return _stats()


@router.post("/reindex", response_model=ReindexResult)
def reindex():
    """Full rebuild from every file in data/raw -- for resyncing after
    files were edited outside the admin panel (e.g. directly on disk),
    not needed for normal create/edit/delete through this API."""
    try:
        store.rebuild_all()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _stats()
