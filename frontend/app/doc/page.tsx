"use client";
import {useEffect, useState} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {FileText} from "lucide-react";

const TABS = [
    {key: "REPORT.md", label: "Project Report"},
    {key: "README.md", label: "README"},
] as const;

export default function DocPage() {
    const [active, setActive] = useState<typeof TABS[number]["key"]>("REPORT.md");
    const [content, setContent] = useState<Record<string, string | null>>({});

    useEffect(() => {
        if (content[active] !== undefined) return;
        fetch(`/docs/${active}`)
            .then(r => r.ok ? r.text() : Promise.reject(new Error(`${r.status}`)))
            .then(text => setContent(c => ({...c, [active]: text})))
            .catch(() => setContent(c => ({...c, [active]: null})));
    }, [active, content]);

    const text = content[active];

    return <>
        <section className="hero">
            <div className="eyebrow">Documentation</div>
            <h1>Report &amp; README</h1>
            <p>The full write-up and technical documentation for this project, rendered directly from the
                repository so it's always current.</p>
        </section>

        <div className="docTabs">
            {TABS.map(t => (
                <button key={t.key} className={`docTab${active === t.key ? " active" : ""}`}
                        onClick={() => setActive(t.key)}>
                    <FileText size={14}/> {t.label}
                </button>
            ))}
        </div>

        <section className="card markdownCard">
            {text === undefined && <div className="hint">Loading…</div>}
            {text === null && <div className="hint">Could not load {active}.</div>}
            {text && <div className="markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
            </div>}
        </section>
    </>;
}
