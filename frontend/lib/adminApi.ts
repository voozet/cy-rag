import {CorpusDocument, CorpusDocumentInput, ReindexResult,} from "../types/api";

export const ADMIN_TOKEN_KEY = "cyberrag_admin_token";

export function getStoredAdminToken(): string {
    if (typeof window === "undefined") return "";
    return window.localStorage.getItem(ADMIN_TOKEN_KEY) || "";
}

export function setStoredAdminToken(token: string) {
    if (typeof window === "undefined") return;
    if (token) window.localStorage.setItem(ADMIN_TOKEN_KEY, token);
    else window.localStorage.removeItem(ADMIN_TOKEN_KEY);
}

// Corpus CRUD/reindex -- gated server-side only when ADMIN_TOKEN is actually
// configured (see require_admin in the backend); sending a token here when
// none is required is harmless, the backend just ignores it.
async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`/api/admin${path}`, {
        ...init,
        headers: {"Content-Type": "application/json", "x-admin-token": token, ...(init?.headers || {})}
    });
    if (!res.ok) {
        let detail = res.statusText;
        try {
            detail = (await res.json()).detail || detail
        } catch {
        }
        const err = new Error(detail) as Error & { status?: number };
        err.status = res.status;
        throw err;
    }
    return res.status === 204 ? (undefined as T) : res.json();
}

export const listDocuments = (token: string) =>
    request<CorpusDocument[]>("/documents", token);

export const getDocument = (slug: string, token: string) =>
    request<CorpusDocument>(`/documents/${encodeURIComponent(slug)}`, token);

export const createDocument = (doc: CorpusDocumentInput, token: string) =>
    request<CorpusDocument>("/documents", token, {method: "POST", body: JSON.stringify(doc)});

export const updateDocument = (slug: string, doc: CorpusDocumentInput, token: string) =>
    request<CorpusDocument>(`/documents/${encodeURIComponent(slug)}`, token, {
        method: "PUT",
        body: JSON.stringify(doc)
    });

export const deleteDocument = (slug: string, token: string) =>
    request<ReindexResult>(`/documents/${encodeURIComponent(slug)}`, token, {method: "DELETE"});

export const triggerReindex = (token: string) =>
    request<ReindexResult>("/reindex", token, {method: "POST"});
