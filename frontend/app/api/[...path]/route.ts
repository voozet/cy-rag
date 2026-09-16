import {NextRequest, NextResponse} from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

async function proxy(req: NextRequest, path: string[]): Promise<NextResponse> {
    const target = `${BACKEND_URL}/api/${path.join("/")}${req.nextUrl.search}`;
    const headers: Record<string, string> = {"Content-Type": "application/json"};
    const token = req.headers.get("x-admin-token");
    if (token) headers["x-admin-token"] = token;

    const hasBody = !["GET", "HEAD"].includes(req.method);
    let res: Response;
    try {
        res = await fetch(target, {
            method: req.method,
            headers,
            body: hasBody ? await req.text() : undefined,
            cache: "no-store",
        });
    } catch {
        return NextResponse.json({detail: "Could not reach the backend service."}, {status: 502});
    }

    const text = await res.text();
    return new NextResponse(text, {
        status: res.status,
        headers: {"Content-Type": res.headers.get("Content-Type") || "application/json"},
    });
}

export async function GET(req: NextRequest, {params}: { params: Promise<{ path: string[] }> }) {
    return proxy(req, (await params).path);
}

export async function POST(req: NextRequest, {params}: { params: Promise<{ path: string[] }> }) {
    return proxy(req, (await params).path);
}

export async function PUT(req: NextRequest, {params}: { params: Promise<{ path: string[] }> }) {
    return proxy(req, (await params).path);
}

export async function DELETE(req: NextRequest, {params}: { params: Promise<{ path: string[] }> }) {
    return proxy(req, (await params).path);
}
