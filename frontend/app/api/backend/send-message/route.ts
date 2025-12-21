import { NextRequest } from "next/server";

const BACKEND_URL = process.env.FASTAPI_URL ?? "http://127.0.0.1:8000";

/**
 * Custom API route that proxies SSE streaming requests to the backend.
 * Next.js rewrites buffer responses, so we need this custom handler
 * to properly stream Server-Sent Events back to the client.
 */
export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const message = searchParams.get("message");
    const session = searchParams.get("session") ?? "default";

    if (!message) {
        return new Response(JSON.stringify({ error: "Message is required" }), {
            status: 400,
            headers: { "Content-Type": "application/json" },
        });
    }

    // Forward the authorization header
    const authHeader = request.headers.get("Authorization");

    const backendUrl = `${BACKEND_URL}/send-message?${new URLSearchParams({
        message,
        session,
    }).toString()}`;

    try {
        const response = await fetch(backendUrl, {
            method: "GET",
            headers: {
                ...(authHeader ? { Authorization: authHeader } : {}),
                Accept: "text/event-stream",
            },
        });

        if (!response.ok) {
            return new Response(
                JSON.stringify({ error: `Backend error: ${response.status}` }),
                {
                    status: response.status,
                    headers: { "Content-Type": "application/json" },
                }
            );
        }

        // Stream the response back to the client
        return new Response(response.body, {
            status: 200,
            headers: {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache, no-transform",
                Connection: "keep-alive",
                "X-Accel-Buffering": "no",
            },
        });
    } catch (error) {
        console.error("Backend proxy error:", error);
        return new Response(
            JSON.stringify({ error: "Failed to connect to backend" }),
            {
                status: 502,
                headers: { "Content-Type": "application/json" },
            }
        );
    }
}
