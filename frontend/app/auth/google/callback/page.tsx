"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/app/providers";
import { withApi } from "@/lib/apiBase";

type CallbackStatus = "loading" | "success" | "error";

function GoogleCallbackContent(): JSX.Element {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { token, isAuthenticated, isInitialised } = useAuth();
    const [status, setStatus] = useState<CallbackStatus>("loading");
    const [message, setMessage] = useState("");

    useEffect(() => {
        // Wait for auth to initialise
        if (!isInitialised) return;

        // If not authenticated, redirect to auth page
        if (!isAuthenticated || !token) {
            router.replace("/auth");
            return;
        }

        async function handleCallback(): Promise<void> {
            const code = searchParams.get("code");
            const state = searchParams.get("state");
            const error = searchParams.get("error");

            if (error) {
                setStatus("error");
                setMessage(`OAuth error: ${error}`);
                return;
            }

            if (!code || !state) {
                setStatus("error");
                setMessage("Missing authorisation code or state");
                return;
            }

            try {
                const params = new URLSearchParams({ code, state });
                const response = await fetch(
                    withApi(`/oauth/google/callback?${params.toString()}`),
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );

                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || "Failed to complete OAuth flow");
                }

                setStatus("success");
                setMessage("Google Calendar connected successfully!");

                // Redirect to settings page after 2 seconds
                setTimeout(() => {
                    router.push("/settings");
                }, 2000);
            } catch (err) {
                setStatus("error");
                setMessage(err instanceof Error ? err.message : "Unknown error");
            }
        }

        void handleCallback();
    }, [searchParams, token, router, isAuthenticated, isInitialised]);

    return (
        <main className="min-h-screen flex items-center justify-center bg-slate-950">
            <div className="text-center p-8">
                {status === "loading" && (
                    <>
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                        <p className="text-slate-300">Completing Google Calendar connection...</p>
                    </>
                )}
                {status === "success" && (
                    <>
                        <div className="text-green-500 text-5xl mb-4">✓</div>
                        <p className="text-green-400 text-lg mb-2">{message}</p>
                        <p className="text-slate-400 text-sm">Redirecting to settings...</p>
                    </>
                )}
                {status === "error" && (
                    <>
                        <div className="text-red-500 text-5xl mb-4">✗</div>
                        <p className="text-red-400 text-lg mb-4">{message}</p>
                        <button
                            onClick={() => router.push("/settings")}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                        >
                            Return to Settings
                        </button>
                    </>
                )}
            </div>
        </main>
    );
}

export default function GoogleCallbackPage(): JSX.Element {
    return (
        <Suspense
            fallback={
                <main className="min-h-screen flex items-center justify-center bg-slate-950">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                </main>
            }
        >
            <GoogleCallbackContent />
        </Suspense>
    );
}
