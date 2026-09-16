"""Evaluation logic shared by scripts/evaluate.py and the /api/evaluation
endpoints, so the CLI and the in-app "Evaluation" page always agree.
"""
import json
from datetime import datetime, timezone

from .agents.workflow import execute
from .config import BASE_DIR

QUERIES_PATH = BASE_DIR / "tests" / "queries.json"
RESULTS_PATH = BASE_DIR / "tests" / "results.json"


def load_queries() -> list[dict]:
    return json.loads(QUERIES_PATH.read_text(encoding="utf-8"))


def run_one(question: str) -> dict:
    return execute(question).model_dump()


def score(query: dict, response: dict) -> dict:
    triage_step = next((a for a in response.get("agents", []) if a["name"] == "triage"), None)
    actual_in_scope = bool(triage_step["details"].get("in_scope")) if triage_step else None
    scope_correct = actual_in_scope == query["expected_in_scope"] if actual_in_scope is not None else None

    actual_answerable = response.get("status") == "success"
    outcome_correct = actual_answerable == query["expected_answerable"]

    grounded, has_citations = None, None
    if actual_answerable:
        cited_ids = {c["id"] for c in response.get("citations", [])}
        analyst_step = next((a for a in response.get("agents", []) if a["name"] == "rag_analyst"), None)
        retrieved_ids = set(analyst_step["details"].get("evidence_ids", [])) if analyst_step else set()
        grounded = cited_ids.issubset(retrieved_ids) if retrieved_ids else None
        has_citations = len(cited_ids) > 0

    return {"scope_correct": scope_correct, "outcome_correct": outcome_correct,
            "grounded": grounded, "has_citations": has_citations}


def run_all() -> list[dict]:
    results = []
    for q in load_queries():
        try:
            response = run_one(q["question"])
            error = None
        except Exception as exc:  # noqa: BLE001 -- surface any failure as a scored row
            response, error = {}, str(exc)
        row = {"id": q["id"], "question": q["question"],
               "expected": {"in_scope": q["expected_in_scope"], "answerable": q["expected_answerable"]},
               "response": response, "error": error}
        row["scores"] = score(q, response) if not error else {}
        results.append(row)
    return results


def summarize(results: list[dict]) -> dict:
    total = len(results)
    scope_ok = sum(1 for r in results if r["scores"].get("scope_correct"))
    outcome_ok = sum(1 for r in results if r["scores"].get("outcome_correct"))
    grounded_checked = [r for r in results if r["scores"].get("grounded") is not None]
    grounded_ok = sum(1 for r in grounded_checked if r["scores"]["grounded"])
    errors = sum(1 for r in results if r["error"])
    return {
        "total": total, "scope_correct": scope_ok, "outcome_correct": outcome_ok,
        "grounded_checked": len(grounded_checked), "grounded_correct": grounded_ok, "errors": errors,
    }


def save_results(results: list[dict]) -> None:
    RESULTS_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def score_and_save(items: list[dict]) -> list[dict]:
    """Given [{id, response, error}] collected by the caller running each
    query one at a time (e.g. the frontend, so it can show live progress),
    look up each query's expected labels, score it, and persist the full
    result set -- same shape and same score() logic as run_all(), just fed
    externally-produced responses instead of running them here."""
    queries_by_id = {q["id"]: q for q in load_queries()}
    results = []
    for item in items:
        q = queries_by_id.get(item["id"])
        if q is None:
            continue  # ignore unknown ids rather than fail the whole save
        response, error = item.get("response") or {}, item.get("error")
        row = {"id": q["id"], "question": q["question"],
               "expected": {"in_scope": q["expected_in_scope"], "answerable": q["expected_answerable"]},
               "response": response, "error": error}
        row["scores"] = score(q, response) if not error else {}
        results.append(row)
    save_results(results)
    return results


def load_saved() -> dict | None:
    if not RESULTS_PATH.exists():
        return None
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    generated_at = datetime.fromtimestamp(RESULTS_PATH.stat().st_mtime, tz=timezone.utc).isoformat()
    return {"results": results, "summary": summarize(results), "generated_at": generated_at}
