from .triage import run as triage
from .rag_analyst import run as analyst
from .verification import run as verifier
from ..schemas import ChatResponse, AgentStep, Citation


def execute(question: str) -> ChatResponse:
    t = triage(question)
    agents = [AgentStep(name="triage", status="completed", summary=(
        "Cybersecurity query detected" if t.get("in_scope") else "Query is outside cybersecurity scope"), details=t)]
    if not t.get("in_scope"):
        agents += [
            AgentStep(name="rag_analyst", status="skipped", summary="Retrieval and generation skipped"),
            AgentStep(name="verification", status="skipped", summary="Verification skipped"),
        ]
        return ChatResponse(status="refused", reason=t.get("reason", "Out of scope"), agents=agents)

    try:
        draft, evidence = analyst(question, t.get("intent", "general cybersecurity"))
    except RuntimeError as exc:
        return ChatResponse(status="error", reason=str(exc), agents=agents)

    agents.append(
        AgentStep(name="rag_analyst", status="completed", summary=f"Retrieved {len(evidence)} evidence chunks",
                  details={"retrieved": len(evidence),
                           "evidence_ids": [e.id for e in evidence],
                           "evidence": [{"id": e.id, "title": e.title, "score": round(e.score, 4)} for e in evidence],
                           "answerable": draft.get("answerable"), "reason": draft.get("reason", "")}))
    if not draft.get("answerable") or not draft.get("answer"):
        agents.append(AgentStep(name="verification", status="skipped",
                                summary="Verification skipped because evidence was insufficient"))
        return ChatResponse(status="refused",
                            reason=draft.get("reason") or
                                   "The knowledge base does not contain sufficient evidence to answer this question reliably.",
                            agents=agents)

    try:
        v = verifier(question, draft["answer"], evidence)
    except RuntimeError as exc:
        return ChatResponse(status="error", reason=str(exc), agents=agents)
    if not v.get("verified"):
        agents.append(
            AgentStep(name="verification", status="failed", summary="Unsupported claim detected; response withheld",
                      details=v))
        return ChatResponse(status="refused",
                            reason=v.get("reason") or
                                   "The generated response could not be fully grounded in the retrieved evidence.",
                            agents=agents)

    agents.append(AgentStep(name="verification", status="passed",
                            summary=f"Verified {len(draft.get('claims', []))} claims with no unsupported claims",
                            details=v))
    evidence_map = {e.id: e for e in evidence}
    cited_ids = draft.get("evidence_ids") or list(evidence_map)
    citations = [
        Citation(id=e.id, title=e.title, source=e.source, url=e.url, section=e.section, text=e.text, score=e.score) for
        eid in cited_ids if (e := evidence_map.get(eid))]
    return ChatResponse(status="success", answer=draft["answer"], grounded=True, citations=citations, agents=agents)
