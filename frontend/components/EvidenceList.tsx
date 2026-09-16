import {Citation} from "../types/api";

export function EvidenceList({items}: { items: Citation[] }) {
    return <div className="sources">{items.map(c => <article className="sourceCard" key={c.id}>
        <div className="sourceTop"><span className="sourceName">{c.source}</span><span
            className="score">score {c.score.toFixed(3)}</span></div>
        <div className="sourceTitle">{c.title}</div>
        <div className="sourceText">{c.text}</div>
        <div className="sourceMeta">{c.section || "Source"} · <a href={c.url} target="_blank" rel="noreferrer">View
            source ↗</a></div>
    </article>)}</div>
}
