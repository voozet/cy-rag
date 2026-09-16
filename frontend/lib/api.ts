import {ChatResponse} from "../types/api";

export async function askCyberRag(question: string): Promise<ChatResponse> {
    const res = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question})
    });
    if (!res.ok) {
        throw new Error((await res.text()) || "Request failed")
    }
    return res.json();
}
