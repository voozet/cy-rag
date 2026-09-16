import {EvaluationPayload, EvaluationQuery} from "../types/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`/api${path}`, {
        ...init,
        headers: {"Content-Type": "application/json", ...(init?.headers || {})},
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

export async function fetchEvaluation(): Promise<EvaluationPayload | null> {
    try {
        return await request<EvaluationPayload>("/evaluation");
    } catch (e) {
        if ((e as Error & { status?: number }).status === 404) return null;
        throw e;
    }
}

export const getEvaluationQueries = () =>
    request<EvaluationQuery[]>("/evaluation/queries");

export const saveEvaluation = (
    items: { id: string; response?: object; error?: string | null }[],
) => request<EvaluationPayload>("/evaluation/save", {method: "POST", body: JSON.stringify({items})});

// One-shot server-side run (blocks until all queries finish -- no live
// progress). The Evaluation page uses getEvaluationQueries + saveEvaluation
// instead, for live per-query progress.
export const runEvaluation = () =>
    request<EvaluationPayload>("/evaluation/run", {method: "POST"});
