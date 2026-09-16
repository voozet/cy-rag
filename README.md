# CyberRAG — Multi-Agent Cybersecurity RAG

A small FastAPI + Next.js application implementing a three-agent, evidence-first cybersecurity RAG workflow.

**Source repository:** [github.com/voozet/cy-rag](https://github.com/voozet/cy-rag)  
**Live demo:** [cyberrag.tech-forum.ir](https://cyberrag.tech-forum.ir) —
[`/`](https://cyberrag.tech-forum.ir) the assistant,
[`/admin`](https://cyberrag.tech-forum.ir/admin) the knowledge-base admin panel,
[`/evaluation`](https://cyberrag.tech-forum.ir/evaluation) test results,
[`/doc`](https://cyberrag.tech-forum.ir/doc) this README and the full report, rendered.

## Architecture

1. **Triage Agent** — checks scope and intent. Out-of-scope queries are refused before retrieval.
2. **RAG Analyst Agent** — retrieves evidence from FAISS and generates a draft answer using only retrieved evidence.
3. **Verification Agent** — independently checks every material claim against the retrieved evidence. Unsupported
   responses are withheld.

## Stack

- FastAPI + Pydantic
- Sentence Transformers + FAISS
- OpenAI-compatible LLM API
- Next.js + TypeScript
- Docker Compose

## Run locally

### Backend

```bash
cd backend
cp .env.example .env
# Set LLM_API_KEY and optionally LLM_BASE_URL / LLM_MODEL
# Set ADMIN_TOKEN to require a password for the admin panel (leave blank to leave it open, unprotected)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The first startup downloads the embedding model and builds the FAISS index from `backend/data/raw/*.md`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Defaults to talking to a backend at `http://localhost:8000` — no env file needed unless your backend
runs somewhere else, in which case set `BACKEND_URL` (e.g. via `.env.local`).

Open http://localhost:3000.

### Docker

```bash
cp backend/.env.example backend/.env
# configure backend/.env

docker compose up --build
```

No frontend env file is needed for Docker — `docker-compose.yml` sets `BACKEND_URL=http://backend:8000`
directly as a runtime variable for the frontend service.

## Add authoritative documents

Put curated `.md` documents in `backend/data/raw/`. Each document can use simple frontmatter:

```text
---
title: Document title
source: NIST
url: https://...
section: Section name
---
Document text...
```

## Admin panel

Visit http://localhost:3000/admin ("Knowledge Base" in the sidebar) to create, edit, or delete corpus
documents from the browser. Every save or delete calls the backend, which rewrites the Markdown file
and **incrementally updates the FAISS index** — only the changed document's chunks are re-embedded
and spliced into the index; every other document's vectors are left untouched. This uses
`faiss.IndexIDMap` with a deterministic per-chunk id (`hash(f"{slug}-{i}")`), so a chunk always maps
to the same vector id across restarts, and `index.remove_ids([...])` can drop exactly one document's
vectors before re-adding its (possibly different number of) new chunks.

- Protected by a shared secret if you want it to be: set `ADMIN_TOKEN` in `backend/.env` to require a
  password. Leaving it **blank leaves the admin API open** (no password needed) rather than disabling
  it — useful for local/demo use where you don't want a login step at all.
- When a token *is* set, the panel asks for it once and stores it in the browser's `localStorage`;
  it's sent as the `X-Admin-Token` header on every request. This is intentionally simple (a shared
  secret, not per-user accounts) — adequate for a local/demo deployment, not a multi-admin production system.
- The corpus can't be emptied via the panel — deleting the last remaining document is rejected with a
  400, since an empty corpus has nothing to index.
- A separate `POST /api/admin/reindex` (the "rebuild index" button) does a **full** rebuild from every
  file in `data/raw/` — useful only if files were ever edited outside the admin panel and need
  resyncing; normal create/edit/delete through the panel never needs it.

Endpoints (require `X-Admin-Token` only if `ADMIN_TOKEN` is configured — see above):
`GET/POST /api/admin/documents`, `GET/PUT/DELETE /api/admin/documents/{slug}`, `POST /api/admin/reindex`.

## API

`POST /api/chat`

```json
{
  "question": "What is the MITRE ATT&CK Valid Accounts technique?"
}
```

The response includes the final answer, supporting evidence, and structured agent execution results.

## Testing & evaluation

`backend/tests/queries.json` has 14 labeled test queries (expected scope + expected answerability).
With the backend dependencies installed and `LLM_API_KEY` configured:

```bash
cd backend
python -m scripts.evaluate            # imports the workflow directly
# or, with `uvicorn app.main:app` already running in another terminal:
python -m scripts.evaluate --via-api
```

This writes the full agent trace and response for every query to `backend/tests/results.json` and
prints a summary (scope accuracy, refuse-vs-answer accuracy, citation groundedness). The same results
are viewable at `/evaluation` in the app itself — deliberately public, not admin-gated, so anyone
viewing the deployed site can see or re-run it without a token. Clicking "Run evaluation now" there
runs each query one at a time from the browser with a live progress log, then scores and saves the
full set — see `GET/POST /api/evaluation*` and `app/evaluation.py`, which both the CLI and the UI
share so results can't drift apart between them.

## Documentation

`/doc` in the app renders this README and `REPORT.md` directly (as tabs), synced from the repo root
by `frontend/scripts/sync-docs.mjs` on every `npm run dev`/`npm run build`.

See `REPORT.md` for the full write-up: problem definition, architecture rationale, evaluation
methodology and results, limitations, and disclosed tools/AI assistance.

The submitted ZIP contains the complete source tree and test artifacts. The same source is available in the
[GitHub repository](https://github.com/voozet/cy-rag).
