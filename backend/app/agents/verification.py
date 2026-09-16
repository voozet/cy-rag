import json
from ..llm.client import chat

SYSTEM = """You are the independent Verification Agent for a cybersecurity RAG system. Verify the proposed answer against ONLY the provided evidence. Check every factual claim. Return JSON only: {verified:boolean, unsupported_claims:[string], invalid_evidence_ids:[string], reason:string}. If any material factual claim is unsupported, verified must be false."""

def run(question: str, answer: str, evidence: list) -> dict:
    payload = {
        "question": question,
        "answer": answer,
        "evidence": [{"id": e.id, "text": e.text, "source": e.source} for e in evidence],
    }
    return json.loads(chat(SYSTEM, json.dumps(payload, ensure_ascii=False), json_mode=True))
