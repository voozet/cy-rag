"use client";
import {useEffect, useRef, useState} from "react";
import {Check, PlayCircle, X} from "lucide-react";
import {AgentTrace} from "../../components/AgentTrace";
import {EvidenceList} from "../../components/EvidenceList";
import {askCyberRag} from "../../lib/api";
import {EvaluationPayload, EvaluationRow} from "../../types/api";
import {fetchEvaluation, getEvaluationQueries, saveEvaluation} from "../../lib/evaluationApi";

function Badge({value, label}: { value: boolean | null; label: string }) {
    if (value === null) return <span className="evalBadge muted">{label}: n/a</span>;
    return <span className={`evalBadge ${value ? "good" : "bad"}`}>
        {value ? <Check size={12}/> : <X size={12}/>} {label}
    </span>;
}

export default function EvaluationPage() {
    const [data, setData] = useState<EvaluationPayload | null | undefined>(undefined); // undefined = loading
    const [error, setError] = useState("");
    const [expanded, setExpanded] = useState<string | null>(null);
    const [running, setRunning] = useState(false);
    const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
    const [log, setLog] = useState<string[]>([]);
    const logContainerRef = useRef<HTMLElement>(null);

    async function load() {
        try {
            setData(await fetchEvaluation());
            setError("");
        } catch (e) {
            setError((e as Error).message);
            setData(null);
        }
    }

    useEffect(() => {
        load();
    }, []);

    useEffect(() => {
        // Scroll only the log box itself -- never the page. scrollIntoView on a
        // sentinel element also drags ancestor scroll containers (the whole
        // page) into view, which is what caused an earlier page-jump bug.
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [log]);

    async function handleRunClick() {
        setRunning(true);
        setError("");
        setLog([]);
        setProgress(null);
        try {
            const queries = await getEvaluationQueries();
            const items: { id: string; response?: object; error?: string | null }[] = [];
            for (let i = 0; i < queries.length; i++) {
                const q = queries[i];
                setProgress({done: i, total: queries.length});
                setLog(l => [...l, `[${i + 1}/${queries.length}] ${q.id}: ${q.question}`]);
                try {
                    const response = await askCyberRag(q.question);
                    items.push({id: q.id, response});
                    setLog(l => [...l, `  -> ${response.status}${response.grounded ? ", grounded" : ""}`]);
                } catch (e) {
                    items.push({id: q.id, error: (e as Error).message});
                    setLog(l => [...l, `  -> error: ${(e as Error).message}`]);
                }
            }
            setProgress({done: queries.length, total: queries.length});
            setLog(l => [...l, "Scoring and saving…"]);
            setData(await saveEvaluation(items));
        } catch (e) {
            setError((e as Error).message);
        } finally {
            setRunning(false);
        }
    }

    const s = data?.summary;

    return <>
        <section className="hero">
            <div className="eyebrow">Test &amp; evaluation</div>
            <h1>Does it actually work?</h1>
            <p>Every query in <code>backend/tests/queries.json</code> run through the live three-agent workflow,
                scored against what each one is expected to do.</p>
        </section>

        <section className="queryFooter" style={{border: "none", marginTop: 22, paddingTop: 0}}>
            <span className="hint">
                {running && progress ? `Running ${progress.done}/${progress.total}…` :
                    data ? `Last run ${new Date(data.generated_at).toLocaleString()}` : ""}
            </span>
            <button className="ask" onClick={handleRunClick} disabled={running}>
                <PlayCircle size={16}/> {running ? "Running…" : "Run evaluation now"}
            </button>
        </section>

        {running && <section className="card evalLog" style={{marginTop: 14}} ref={logContainerRef}>
            {log.map((line, i) => <div key={i} className="evalLogLine">{line}</div>)}
        </section>}

        {error && <div className="card" style={{marginTop: 18, color: "var(--bad)"}}>{error}</div>}

        {data === undefined && !running && <div className="hint" style={{marginTop: 18}}>Loading…</div>}

        {data === null && !error && !running && <div className="card" style={{marginTop: 18}}>
            <div className="cardTitle">No evaluation has been run yet</div>
            <p className="hint" style={{marginTop: 8}}>Click "Run evaluation now" above, or run
                <code> python -m scripts.evaluate</code> from <code>backend/</code>.</p>
        </div>}

        {data && s && <>
            <section className="adminGrid" style={{gridTemplateColumns: "repeat(4, 1fr)", marginTop: 18}}>
                <div className="card">
                    <div className="hint">Scope accuracy</div>
                    <div className="statNum">{s.scope_correct}/{s.total}</div>
                </div>
                <div className="card">
                    <div className="hint">Outcome accuracy</div>
                    <div className="statNum">{s.outcome_correct}/{s.total}</div>
                </div>
                <div className="card">
                    <div className="hint">Grounded (of answered)</div>
                    <div className="statNum">{s.grounded_correct}/{s.grounded_checked}</div>
                </div>
                <div className="card">
                    <div className="hint">Errors</div>
                    <div className="statNum" style={{color: s.errors ? "var(--bad)" : undefined}}>{s.errors}</div>
                </div>
            </section>

            <section className="card" style={{marginTop: 18, padding: 0, overflow: "hidden"}}>
                {data.results.map((row: EvaluationRow) => {
                    const isOpen = expanded === row.id;
                    const statusLabel = row.error ? "error" : row.response.status || "?";
                    return <div key={row.id} className="evalRow">
                        <div className="evalRowHead" onClick={() => setExpanded(isOpen ? null : row.id)}>
                            <div className="evalRowMain">
                                <span className="evalId">{row.id}</span>
                                <span className="evalQuestion">{row.question}</span>
                            </div>
                            <div className="evalRowBadges">
                                <span
                                    className={`badge ${statusLabel === "success" ? "good" : statusLabel === "refused" ? "" : "bad"}`}>{statusLabel}</span>
                                <Badge value={row.scores.scope_correct} label="scope"/>
                                <Badge value={row.scores.outcome_correct} label="outcome"/>
                                <Badge value={row.scores.grounded} label="grounded"/>
                            </div>
                        </div>
                        {isOpen && <div className="evalRowBody">
                            {row.error && <div className="refusal">Error: {row.error}</div>}
                            {!row.error && <>
                                <div style={{display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 14}}>
                                    <span className="hint">Expected: in_scope={String(row.expected.in_scope)}, answerable={String(row.expected.answerable)}</span>
                                </div>
                                {row.response.answer ? <div className="answer">{row.response.answer}</div> :
                                    <div className="refusal">{row.response.reason}</div>}
                                {!!row.response.citations?.length && <div style={{marginTop: 14}}>
                                    <div className="cardTitle" style={{marginBottom: 8}}>Supporting evidence</div>
                                    <EvidenceList items={row.response.citations}/>
                                </div>}
                                {!!row.response.agents?.length && <div style={{marginTop: 14}}>
                                    <div className="cardTitle" style={{marginBottom: 8}}>Agent execution</div>
                                    <AgentTrace steps={row.response.agents}/>
                                </div>}
                            </>}
                        </div>}
                    </div>;
                })}
            </section>
        </>}
    </>;
}
