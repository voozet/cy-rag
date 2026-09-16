import json

from ..llm.client import chat
from ..rag.index import store

SYSTEM = """You are the RAG Analyst Agent in a cybersecurity system. You may use ONLY the supplied evidence. Never use pretrained knowledge to fill gaps. If evidence is insufficient, set answerable=false. Minor typos or grammatical slips in the question (e.g. a dropped first letter) do not make it unanswerable -- interpret the evident intent and answer normally if the evidence supports it. Short or concise questions are also answerable when the supplied evidence clearly contains the referenced concept, phase, technique, or recommendation. Do not call a question vague merely because it is short; use the evidence and the evident referent to answer it. Return JSON only with: {answerable:boolean, answer:string, claims:[string], evidence_ids:[string], reason:string}. `reason` is always required: if answerable is true, briefly note which evidence supported the answer; if false, explain specifically what was missing or ambiguous. Each factual claim must be supported by one or more supplied evidence records. Do not invent citations or facts."""


def run(question: str, intent: str) -> tuple[dict, list]:
    evidence = store.search(question)
    evidence_payload = [
        {"id": e.id, "title": e.title, "source": e.source, "section": e.section, "text": e.text,
         "score": round(e.score, 4)}
        for e in evidence
    ]
    prompt = json.dumps({"question": question, "intent": intent, "evidence": evidence_payload}, ensure_ascii=False)
    result = json.loads(chat(SYSTEM, prompt, json_mode=True))
    return result, evidence
