import {AgentStep} from "../types/api";

const labels = {triage: "Triage Agent", rag_analyst: "RAG Analyst Agent", verification: "Verification Agent"};

export function AgentTrace({steps}: { steps: AgentStep[] }) {
    return <div className="trace">{steps.map((s) => <div className="step" key={s.name}>
        <div className="stepTop"><span className="stepName">{labels[s.name]}</span><span
            className="stepStatus">{s.status === "passed" || s.status === "completed" ? "✓" : s.status === "failed" ? "✕" : "—"}</span>
        </div>
        <div className="stepSummary">{s.summary}</div>
        {s.details && Object.keys(s.details).length > 0 &&
            <pre className="stepDetails">{JSON.stringify(s.details, null, 2)}</pre>}</div>)}</div>
}
