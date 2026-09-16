export type Citation = {
    id: string;
    title: string;
    source: string;
    url: string;
    section?: string | null;
    text: string;
    score: number
};
export type AgentStep = {
    name: "triage" | "rag_analyst" | "verification";
    status: "completed" | "skipped" | "passed" | "failed";
    summary: string;
    details?: Record<string, unknown>
};
export type ChatResponse = {
    status: "success" | "refused" | "error";
    answer?: string | null;
    reason?: string | null;
    grounded: boolean;
    citations: Citation[];
    agents: AgentStep[]
};

export type CorpusDocument = {
    slug: string;
    title: string;
    source: string;
    url: string;
    section: string;
    text: string;
    word_count: number;
    chunks: number
};

export type CorpusDocumentInput = {
    slug?: string;
    title: string;
    source: string;
    url: string;
    section: string;
    text: string
};

export type ReindexResult = { reindexed: boolean; chunks: number; documents: number };

export type EvaluationScores = {
    scope_correct: boolean | null;
    outcome_correct: boolean | null;
    grounded: boolean | null;
    has_citations: boolean | null
};

export type EvaluationRow = {
    id: string;
    question: string;
    expected: { in_scope: boolean; answerable: boolean };
    response: Partial<ChatResponse>;
    error: string | null;
    scores: EvaluationScores
};

export type EvaluationSummary = {
    total: number;
    scope_correct: number;
    outcome_correct: number;
    grounded_checked: number;
    grounded_correct: number;
    errors: number
};

export type EvaluationPayload = { results: EvaluationRow[]; summary: EvaluationSummary; generated_at: string };

export type EvaluationQuery = {
    id: string;
    question: string;
    expected_in_scope: boolean;
    expected_answerable: boolean;
    notes?: string
};
