import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .admin.router import router as admin_router
from .config import settings
from .schemas import QueryRequest, ChatResponse, EvaluationPayload, EvaluationSaveRequest
from .agents.workflow import execute
from . import evaluation

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TQDM_DISABLE"] = "1"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(admin_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: QueryRequest):
    return execute(request.question)


@app.get("/api/evaluation", response_model=EvaluationPayload)
def get_evaluation():
    saved = evaluation.load_saved()
    if saved is None:
        raise HTTPException(
            status_code=404,
            detail="No evaluation has been run yet. Run scripts/evaluate.py or use the /evaluation page.",
        )
    return saved


@app.get("/api/evaluation/queries")
def get_evaluation_queries():
    return evaluation.load_queries()


@app.post("/api/evaluation/save", response_model=EvaluationPayload)
def save_evaluation(payload: EvaluationSaveRequest):
    evaluation.score_and_save([item.model_dump() for item in payload.items])
    return evaluation.load_saved()


@app.post("/api/evaluation/run", response_model=EvaluationPayload)
def run_evaluation():
    results = evaluation.run_all()
    evaluation.save_results(results)
    return evaluation.load_saved()
