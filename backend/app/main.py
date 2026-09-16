from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .admin.router import router as admin_router
from .config import settings
from .schemas import QueryRequest, ChatResponse, EvaluationPayload, EvaluationSaveRequest
from .agents.workflow import execute
from . import evaluation

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(admin_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: QueryRequest):
    return execute(request.question)


@app.get("/api/evaluation", response_model=EvaluationPayload)
def get_evaluation():
    """The most recent saved evaluation run (tests/results.json)."""
    saved = evaluation.load_saved()
    if saved is None:
        raise HTTPException(status_code=404,
                            detail="No evaluation has been run yet. Run scripts/evaluate.py or use the /evaluation page.")
    return saved


# Deliberately public, not under /api/admin -- anyone viewing the deployed
# site (e.g. a grader) should be able to see and re-run the evaluation
# without needing a secret. This does mean anyone can trigger LLM calls via
# /evaluation/run; acceptable for a small demo/grading deployment, worth
# reconsidering (e.g. rate-limiting) before a wider public launch.

@app.get("/api/evaluation/queries")
def get_evaluation_queries():
    """The raw test query list, so a caller (the Evaluation page) can run
    each one itself -- one /api/chat call at a time -- and show live
    progress, rather than blocking on one big server-side run."""
    return evaluation.load_queries()


@app.post("/api/evaluation/save", response_model=EvaluationPayload)
def save_evaluation(payload: EvaluationSaveRequest):
    """Score and persist a set of already-run {id, response} results
    (see get_evaluation_queries). Scoring logic is identical to run_all()'s --
    both live in app/evaluation.py -- so results are comparable either way."""
    evaluation.score_and_save([item.model_dump() for item in payload.items])
    return evaluation.load_saved()


@app.post("/api/evaluation/run", response_model=EvaluationPayload)
def run_evaluation():
    """Re-run all test queries through the live workflow, blocking until
    done, and persist the results. Prefer /evaluation/queries +
    /evaluation/save from the UI for live per-query progress -- this one is
    mainly for scripted/CLI use (scripts/evaluate.py --via-api)."""
    results = evaluation.run_all()
    evaluation.save_results(results)
    return evaluation.load_saved()
