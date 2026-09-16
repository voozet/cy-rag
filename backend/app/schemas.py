from typing import Literal
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)

class Citation(BaseModel):
    id: str
    title: str
    source: str
    url: str
    section: str | None = None
    text: str
    score: float

class AgentStep(BaseModel):
    name: Literal["triage", "rag_analyst", "verification"]
    status: Literal["completed", "skipped", "passed", "failed"]
    summary: str
    details: dict = Field(default_factory=dict)

class ChatResponse(BaseModel):
    status: Literal["success", "refused", "error"]
    answer: str | None = None
    reason: str | None = None
    grounded: bool = False
    citations: list[Citation] = Field(default_factory=list)
    agents: list[AgentStep] = Field(default_factory=list)


class CorpusDocument(BaseModel):
    slug: str
    title: str
    source: str
    url: str = ""
    section: str = ""
    text: str
    word_count: int = 0
    chunks: int = 0


class CorpusDocumentCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=100)
    url: str = ""
    section: str = ""
    text: str = Field(min_length=1)


class CorpusDocumentUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=100)
    url: str = ""
    section: str = ""
    text: str = Field(min_length=1)


class ReindexResult(BaseModel):
    reindexed: bool
    chunks: int
    documents: int


class EvaluationScores(BaseModel):
    scope_correct: bool | None = None
    outcome_correct: bool | None = None
    grounded: bool | None = None
    has_citations: bool | None = None


class EvaluationRow(BaseModel):
    id: str
    question: str
    expected: dict
    response: dict = Field(default_factory=dict)
    error: str | None = None
    scores: EvaluationScores = Field(default_factory=EvaluationScores)


class EvaluationSummary(BaseModel):
    total: int
    scope_correct: int
    outcome_correct: int
    grounded_checked: int
    grounded_correct: int
    errors: int


class EvaluationPayload(BaseModel):
    results: list[EvaluationRow]
    summary: EvaluationSummary
    generated_at: str


class EvaluationRunItem(BaseModel):
    id: str
    response: dict = Field(default_factory=dict)
    error: str | None = None


class EvaluationSaveRequest(BaseModel):
    items: list[EvaluationRunItem]
