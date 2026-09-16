# CyberRAG — Multi-Agent RAG for Cybersecurity Question Answering

**Source repository:** [https://github.com/voozet/cy-rag](https://github.com/voozet/cy-rag)  
**Live demo:** [https://cyberrag.tech-forum.ir](https://cyberrag.tech-forum.ir)

## 1. Problem & Use Case

Security analysts and IT generalists need quick, trustworthy answers to cybersecurity questions without a
general-purpose LLM's risk of hallucinated specifics (wrong technique IDs, invented mitigations) or stale pretrained
knowledge. CyberRAG is a **grounded-only** assistant: it answers using *only* retrieved evidence from a curated document
set (NIST, MITRE ATT&CK, CISA, OWASP), explicitly refusing when evidence is missing, insufficient, or off-topic. Target
use case: a first-line SOC/IT assistant, not a replacement for expert judgment.

## 2. Data & Pipeline

Seven Markdown documents in `backend/data/raw/` (MITRE ATT&CK T1078, NIST SP 800-61 & SP 800-63B, CISA phishing &
ransomware guidance, OWASP SQL Injection, CrowdStrike AI-agent security), each with YAML frontmatter
(title/source/url/section) carried through to citations. Six are condensed paraphrases of public guidance (URLs
preserved); for a production system these would be the full source text.

- **Chunking**: ~900-char, sentence-boundary-aware, 150-char overlap.
- **Embeddings**: `BAAI/bge-small-en-v1.5` (fast, no GPU needed at this scale).
- **Vector store**: FAISS `IndexIDMap` over `IndexFlatIP` (cosine similarity), keyed by a deterministic per-chunk id —
  this is what lets the admin panel splice a single document's vectors in/out (`remove_ids`/`add_with_ids`) without
  touching or re-embedding the rest of the corpus.
- **Retrieval**: pure cosine similarity under-scores short, terminology-heavy questions (e.g. one naming an exact NIST
  phase but sharing little surface text with the source paragraph). Retrieval blends in a token-overlap and
  exact-phrase-match signal alongside cosine similarity to catch these; accepted candidates are re-ranked by the
  combined score and truncated to top 5.

**Admin panel** (`/admin`): create/edit/delete corpus documents from the browser; each change incrementally re-indexes
only that document.

## 3. Multi-Agent Architecture

A **fixed sequential pipeline**, each stage gating the next — chosen over a dynamic orchestrator because the task
decomposes cleanly into three independent, always-same-order checks, making it easier to reason about and debug than a
more flexible graph, at no capability cost here.

1. **Triage** — classifies topic relevance only, before retrieval; out-of-scope questions never reach the vector store.
2. **RAG Analyst** — retrieves evidence, drafts an answer using *only* that evidence, returns `answerable:false` rather
   than filling gaps from pretrained knowledge.
3. **Verification** — an independent second LLM pass checking the *draft* against the *same* evidence; catches drift a
   single pass would miss.

Agents communicate via typed hand-offs (`AgentStep`, `Citation`, `ChatResponse`), not free text. A
successful answer is returned with a `grounded:true` flag and a structured citation list (title,
source, URL, section, and the exact passage) restricted to only the evidence actually used — so every
claim in an answer is traceable to a specific source, not just asserted. Every response also includes
a full `agents` trace (visible in the UI), so a refusal always traces to one of three distinct causes:
out-of-scope, insufficient evidence, or failed verification — not one generic rejection.

## 4. Testing & Evaluation

`backend/tests/queries.json` — 14 labeled queries: direct factual lookups, cross-document synthesis, and four refusal
categories (out-of-scope ×2, in-scope-but-unsupported, unanswerable/over-broad, time-sensitive). Runnable via
`python -m scripts.evaluate` or live at `/evaluation` (public — no login needed to view or re-run), scored on scope
accuracy, outcome accuracy (answer-vs-refuse matches expectation), and groundedness (every citation traces to real
retrieved evidence).

**Results:** Scope accuracy 14/14 (100%). Outcome accuracy 13/14 (93%). Groundedness 10/10 of successful answers (100%),
zero errors. The one mismatch (Q9, "stop *every* hacker from attacking my company") is a design question, not a bug: the
system answered with genuinely grounded general best practices rather than refusing outright, correctly declining to
promise the impossible absolute — a defensible choice, though a stricter system would flag unbounded phrasing and refuse
instead. Q13/14 (added after live-adding a new document via the admin panel) confirm end-to-end retrieval of newly
indexed content, not just at the file-write level.

## 5. Discussion

**A real failure found and fixed during testing:** short, phrase-heavy questions naming an exact source term (e.g. "the
final phase... emphasizes on what?") were initially refused as "too vague" — Triage's prompt rejected terse phrasing
before retrieval ran, and separately, cosine similarity under-scored short queries against longer source paragraphs.
Fixed at the actual layer in each case (Sections 2–3), not papered over — confirmed by a full re-run afterward, not just
the motivating case. The agent trace was what made this diagnosable at all.

**Limitations**: retrieval's scoring weights are hand-tuned, not calibrated against labeled relevance data; the Verifier
and Analyst share a model family and so may share blind spots; seven documents exercises the pipeline but won't surface
disambiguation failures a larger, overlapping corpus would.

**Possible improvements**: a cross-encoder re-ranker in place of the hand-tuned lexical heuristic; a runtime citation-ID
guard (currently checked only at evaluation time); a held-out query set so retrieval weights aren't tuned against the
same queries used to score them.

## 6. Tools, Resources & AI Assistance Disclosure

FastAPI, Pydantic, sentence-transformers, FAISS, an OpenAI-compatible LLM API, Next.js/TypeScript, and Docker Compose.
Embedding model `BAAI/bge-small-en-v1.5`; LLM via `LLM_MODEL` (default `gpt-4o-mini`). Data sources: MITRE ATT&CK, NIST,
CISA, OWASP, CrowdStrike. Claude (Anthropic) was used throughout development — scaffolding the codebase and agent
workflow.


## Submission

The complete source code, test queries, evaluation results, documentation, and deployment configuration are included in the submitted ZIP archive. The project is also available at [https://github.com/voozet/cy-rag](https://github.com/voozet/cy-rag), and the deployed application is available at [https://cyberrag.tech-forum.ir](https://cyberrag.tech-forum.ir).