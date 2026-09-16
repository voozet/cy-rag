"use client";
import {useEffect, useState} from "react";
import {Lock, Plus, RefreshCw, Trash2} from "lucide-react";
import {CorpusDocument, CorpusDocumentInput} from "../../types/api";
import {
    createDocument,
    deleteDocument,
    getStoredAdminToken,
    listDocuments,
    setStoredAdminToken,
    triggerReindex,
    updateDocument,
} from "../../lib/adminApi";

const emptyForm: CorpusDocumentInput = {slug: "", title: "", source: "", url: "", section: "", text: ""};

function slugify(title: string) {
    return title.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

export default function AdminPage() {
    const [token, setToken] = useState<string | null>(null); // null = not yet determined
    const [tokenInput, setTokenInput] = useState("");
    const [needsToken, setNeedsToken] = useState(false);
    const [authError, setAuthError] = useState("");
    const [docs, setDocs] = useState<CorpusDocument[] | null>(null);
    const [selected, setSelected] = useState<string | null>(null); // slug being edited, or "new"
    const [form, setForm] = useState<CorpusDocumentInput>(emptyForm);
    const [saving, setSaving] = useState(false);
    const [reindexing, setReindexing] = useState(false);
    const [error, setError] = useState("");
    const [status, setStatus] = useState("");

    // Always attempt a load on mount, with whatever token is stored (possibly
    // none) -- if the backend has no ADMIN_TOKEN configured, this succeeds
    // with an empty token and the panel opens straight away, no prompt.
    // Only a real 401 (a token IS required and we don't have the right one)
    // shows the gate.
    useEffect(() => {
        attemptLoad(getStoredAdminToken());
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    async function attemptLoad(candidateToken: string) {
        try {
            const list = await listDocuments(candidateToken);
            setDocs(list);
            setToken(candidateToken);
            setNeedsToken(false);
            setAuthError("");
        } catch (e) {
            const err = e as Error & { status?: number };
            if (err.status === 401) {
                setStoredAdminToken("");
                setToken(null);
                setNeedsToken(true);
                setAuthError(err.message);
            } else {
                setError(err.message);
            }
        }
    }

    async function refresh() {
        if (token === null) return;
        await attemptLoad(token);
    }

    function submitToken() {
        setStoredAdminToken(tokenInput.trim());
        attemptLoad(tokenInput.trim());
    }

    function startCreate() {
        setSelected("new");
        setForm(emptyForm);
        setError("");
        setStatus("");
    }

    function startEdit(doc: CorpusDocument) {
        setSelected(doc.slug);
        setForm({
            slug: doc.slug,
            title: doc.title,
            source: doc.source,
            url: doc.url,
            section: doc.section,
            text: doc.text
        });
        setError("");
        setStatus("");
    }

    async function save() {
        if (!form.title.trim() || !form.source.trim() || !form.text.trim()) {
            setError("Title, source, and text are required.");
            return;
        }
        if (token === null) return;
        setSaving(true);
        setError("");
        try {
            if (selected === "new") {
                const slug = (form.slug || slugify(form.title)).trim();
                if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug)) {
                    setError("Slug must be lowercase letters, numbers, and hyphens only.");
                    setSaving(false);
                    return;
                }
                const created = await createDocument({...form, slug}, token);
                setStatus(`Created "${created.title}" — ${created.chunks} chunk${created.chunks === 1 ? "" : "s"} added to the index.`);
                setSelected(created.slug);
            } else if (selected) {
                const updated = await updateDocument(selected, form, token);
                setStatus(`Saved "${updated.title}" — re-indexed ${updated.chunks} chunk${updated.chunks === 1 ? "" : "s"} for this document only.`);
            }
            await refresh();
        } catch (e) {
            setError((e as Error).message);
        } finally {
            setSaving(false);
        }
    }

    async function remove(slug: string) {
        if (token === null) return;
        if (!confirm(`Delete "${slug}" from the corpus? The index will be rebuilt immediately.`)) return;
        setError("");
        try {
            const result = await deleteDocument(slug, token);
            setStatus(`Deleted. Corpus now has ${result.documents} documents (${result.chunks} chunks).`);
            if (selected === slug) {
                setSelected(null);
                setForm(emptyForm);
            }
            await refresh();
        } catch (e) {
            setError((e as Error).message);
        }
    }

    async function manualReindex() {
        if (token === null) return;
        setError("");
        setReindexing(true);
        try {
            const result = await triggerReindex(token);
            setStatus(`Reindexed: ${result.chunks} chunks across ${result.documents} documents.`);
        } catch (e) {
            setError((e as Error).message);
        } finally {
            setReindexing(false);
        }
    }

    if (needsToken) {
        return <>
            <section className="hero">
                <div className="eyebrow">Knowledge base</div>
                <h1>Admin access required</h1>
                <p>Enter the admin token configured as <code>ADMIN_TOKEN</code> in the backend to manage the corpus.</p>
            </section>
            <section className="queryBox" style={{marginTop: 30}}>
                <input type="password" placeholder="Admin token" value={tokenInput}
                       onChange={e => setTokenInput(e.target.value)}
                       onKeyDown={e => e.key === "Enter" && submitToken()}
                       style={{
                           width: "100%", background: "transparent", border: 0, outline: 0,
                           color: "var(--text)", fontSize: 15, padding: "10px 4px"
                       }}/>
                <div className="queryFooter">
                    <span className="hint">{authError || "Stored locally in this browser only."}</span>
                    <button className="ask" onClick={submitToken} disabled={!tokenInput.trim()}>
                        <Lock size={16}/> Unlock
                    </button>
                </div>
            </section>
        </>;
    }

    if (token === null) {
        return <div className="hint" style={{marginTop: 30}}>Loading…</div>;
    }

    return <>
        <section className="hero">
            <div className="eyebrow">Knowledge base</div>
            <h1>Manage the corpus</h1>
            <p>Create, edit, or remove documents. Saving embeds and indexes only the document you
                changed — every other document's vectors are left untouched.</p>
        </section>

        {status && <div className="card" style={{marginTop: 18, color: "var(--good)"}}>{status}</div>}
        {error && <div className="card" style={{marginTop: 18, color: "var(--bad)"}}>{error}</div>}

        <section className="adminGrid">
            <div className="card docList">
                <div className="answerHeader">
                    <div className="cardTitle">Documents{docs ? ` (${docs.length})` : ""}</div>
                    <div style={{display: "flex", gap: 8}}>
                        <button className="iconBtn" title="Rebuild index" onClick={manualReindex}
                                disabled={reindexing}>
                            <RefreshCw size={14} className={reindexing ? "spin" : ""}/>
                        </button>
                        <button className="iconBtn" title="New document" onClick={startCreate}>
                            <Plus size={14}/>
                        </button>
                    </div>
                </div>
                {docs === null && <div className="hint">Loading…</div>}
                {docs?.map(d => (
                    <div key={d.slug} className={`docItem${selected === d.slug ? " active" : ""}`}
                         onClick={() => startEdit(d)}>
                        <div>
                            <div className="docTitle">{d.title}</div>
                            <div
                                className="hint">{d.source} · {d.chunks} chunk{d.chunks === 1 ? "" : "s"} · {d.slug}</div>
                        </div>
                        <button className="iconBtn" title="Delete"
                                onClick={e => {
                                    e.stopPropagation();
                                    remove(d.slug);
                                }}>
                            <Trash2 size={14}/>
                        </button>
                    </div>
                ))}
                {docs?.length === 0 && <div className="hint">No documents yet.</div>}
            </div>

            <div className="card">
                {!selected && <div className="hint">Select a document to edit, or create a new one.</div>}
                {selected && <div className="formGrid">
                    <div className="formRow">
                        <label>Slug {selected !== "new" && <span className="hint">(fixed after creation)</span>}</label>
                        <input value={selected === "new" ? form.slug : selected} disabled={selected !== "new"}
                               placeholder={form.title ? slugify(form.title) : "auto-generated-from-title"}
                               onChange={e => setForm({...form, slug: slugify(e.target.value)})}/>
                    </div>
                    <div className="formRow">
                        <label>Title</label>
                        <input value={form.title} onChange={e => setForm({...form, title: e.target.value})}/>
                    </div>
                    <div className="formRowSplit">
                        <div className="formRow">
                            <label>Source</label>
                            <input value={form.source} onChange={e => setForm({...form, source: e.target.value})}
                                   placeholder="NIST, MITRE ATT&CK, CISA, OWASP…"/>
                        </div>
                        <div className="formRow">
                            <label>Section</label>
                            <input value={form.section}
                                   onChange={e => setForm({...form, section: e.target.value})}/>
                        </div>
                    </div>
                    <div className="formRow">
                        <label>Source URL</label>
                        <input value={form.url} onChange={e => setForm({...form, url: e.target.value})}/>
                    </div>
                    <div className="formRow">
                        <label>Text</label>
                        <textarea className="adminTextarea" value={form.text}
                                  onChange={e => setForm({...form, text: e.target.value})}/>
                    </div>
                    <div className="queryFooter" style={{border: "none", paddingTop: 4}}>
                        <span className="hint">Only this document is re-embedded — everything else is untouched.</span>
                        <button className="ask" onClick={save} disabled={saving}>
                            {saving ? "Saving…" : "Save & index"}
                        </button>
                    </div>
                </div>}
            </div>
        </section>
    </>;
}
