"""
Evaluation harness for CyberRAG.

Runs every query in tests/queries.json through the full agent workflow,
records the raw output, and scores it against simple, auditable criteria:

  - scope_correct:      did Triage's in_scope decision match expected_in_scope?
  - outcome_correct:    did the final status (success vs refused) match whether
                         the question was expected to be answerable?
  - grounded:           for successful answers, did every citation actually
                         come from the retrieved evidence (no fabricated IDs)?
  - has_citations:      for successful answers, is at least one source cited?

The scoring/run logic lives in app/evaluation.py and is shared with the
in-app "Evaluation" page (GET/POST /api/evaluation*) -- this script is a
thin CLI wrapper around the same code, so results never drift between the
two. Results are written to tests/results.json either way.

Usage:
    cd backend
    python -m scripts.evaluate
    # or, to exercise the real HTTP layer against a running server:
    python -m scripts.evaluate --via-api
"""
import argparse

from app.evaluation import load_queries, run_one, score, save_results, summarize, run_all


def run_via_api(question: str, base_url: str) -> dict:
    import requests
    r = requests.post(f"{base_url}/api/chat", json={"question": question}, timeout=60)
    r.raise_for_status()
    return r.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--via-api", action="store_true",
                        help="Call a running FastAPI server instead of importing the workflow directly")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    if args.via_api:
        results = []
        for q in load_queries():
            try:
                response = run_via_api(q["question"], args.base_url)
                error = None
            except Exception as exc:  # noqa: BLE001 -- surface any failure as a scored row
                response, error = {}, str(exc)
            row = {"id": q["id"], "question": q["question"],
                   "expected": {"in_scope": q["expected_in_scope"], "answerable": q["expected_answerable"]},
                   "response": response, "error": error}
            row["scores"] = score(q, response) if not error else {}
            results.append(row)
    else:
        results = run_all()

    save_results(results)
    s = summarize(results)

    print(f"Queries run:            {s['total']}")
    print(f"Triage scope correct:   {s['scope_correct']}/{s['total']}")
    print(f"Outcome correct:        {s['outcome_correct']}/{s['total']}  (refuse vs answer matched expectation)")
    if s["grounded_checked"]:
        print(f"Citations grounded:     {s['grounded_correct']}/{s['grounded_checked']}  (of successful answers)")
    if s["errors"]:
        print(f"Errors (see results.json): {s['errors']}")
    from app.evaluation import RESULTS_PATH
    print(f"\nFull results written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
