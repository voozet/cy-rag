"use client";
import {useState} from "react";
import {ArrowUp, ShieldCheck} from "lucide-react";
import {EvidenceList} from "../components/EvidenceList";
import {AgentTrace} from "../components/AgentTrace";
import {askCyberRag} from "../lib/api";
import {ChatResponse} from "../types/api";


const example = "An attacker obtained valid credentials and used them to access an internal system. What MITRE ATT&CK technique is relevant?";
export default function Home() {
    const [question, setQuestion] = useState("");
    const [result, setResult] = useState<ChatResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function submit() {
        if (!question.trim() || loading) return;
        setLoading(true);
        setError("");
        try {
            setResult(await askCyberRag(question.trim()))
        } catch (e) {
            setError(e instanceof Error ? e.message : "Request failed")
        } finally {
            setLoading(false)
        }
    }

    return <>
        <section className="hero">
            <div className="eyebrow">Evidence-first cybersecurity intelligence</div>
            <h1>Ask. Retrieve. Verify.</h1><p>A three-agent RAG system that answers cybersecurity questions using
            only evidence retrieved from its knowledge base.</p></section>
        <section className="queryBox"><textarea value={question} onChange={e => setQuestion(e.target.value)}
                                                onKeyDown={e => {
                                                    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") submit()
                                                }}
                                                placeholder="Describe an incident or ask a cybersecurity question..."/>
            <div className="queryFooter"><span className="hint">Try: {example}</span>
                <button className="ask" disabled={!question.trim() || loading}
                        onClick={submit}>{loading ? "Analyzing…" : <><ArrowUp size={16}/> Analyze</>}</button>
            </div>
        </section>
        {error &&
            <div className="card" style={{marginTop: 18, color: "var(--bad)"}}>{error}</div>}{!result && !loading &&
        <div className="empty"><ShieldCheck size={28}/>
            <div style={{marginTop: 10, color: "var(--text)"}}>Ready for a grounded cybersecurity question</div>
            <div style={{marginTop: 5}}>The system refuses out-of-scope or unsupported questions.</div>
        </div>}{result && <section className="result">
        <div className="card">
            <div className="answerHeader">
                <div className="cardTitle">Response</div>
                <span
                    className={`badge ${result.grounded ? "good" : "bad"}`}>{result.grounded ? "Grounded ✓" : result.status === "refused" ? "Response withheld" : "Error"}</span>
            </div>
            {result.answer ? <div className="answer">{result.answer}</div> :
                <div className="refusal">{result.reason}</div>}</div>
        {result.citations.length > 0 && <div className="card">
            <div className="answerHeader">
                <div className="cardTitle">Supporting evidence</div>
                <span className="hint">{result.citations.length} passages</span></div>
            <EvidenceList items={result.citations}/></div>}
        <div className="card">
            <div className="answerHeader">
                <div className="cardTitle">Agent execution</div>
                <span className="hint">3 stages</span></div>
            <AgentTrace steps={result.agents}/></div>
    </section>}</>
}
