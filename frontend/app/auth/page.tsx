"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiBase } from "@/lib/apiBase";
import { getStoredAuth, setStoredAuth } from "@/lib/authStorage";

type AuthMode = "login" | "register";

export default function AuthPage(): JSX.Element {
    const [mode, setMode] = useState<AuthMode>("login");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const router = useRouter();

    useEffect(() => {
        const stored = getStoredAuth();
        if (stored.userId) {
            router.replace("/");
        }
    }, [router]);

    const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
        event.preventDefault();
        setError(null);
        setIsSubmitting(true);

        const endpoint = mode === "login" ? "/login" : "/register";
        try {
            const response = await fetch(`${apiBase}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            if (mode === "register" && response.status === 409) {
                setError("Email already registered");
                return;
            }

            if (mode === "login" && response.status === 401) {
                setError("Invalid email or password");
                return;
            }

            if (!response.ok) {
                setError("Something went wrong. Please try again.");
                return;
            }

            const payload: { status?: string; user_id?: string } = await response.json();
            if (!payload?.user_id) {
                setError("Unexpected response from server.");
                return;
            }

            setStoredAuth(payload.user_id, email);
            router.replace("/");
        } catch (submitError) {
            console.error(submitError);
            setError("Unable to reach the server. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const toggleMode = (nextMode: AuthMode): void => {
        setMode(nextMode);
        setError(null);
    };

    const submitLabel = mode === "login" ? "Login" : "Create account";

    return (
        <main className="min-h-screen w-full bg-slate-950 text-white flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-2xl">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <p className="text-sm text-slate-400">Room Booking Agent</p>
                        <h1 className="text-2xl font-semibold">Welcome back</h1>
                    </div>
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={() => toggleMode("login")}
                            className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                                mode === "login"
                                    ? "bg-blue-600 text-white"
                                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                            }`}
                        >
                            Login
                        </button>
                        <button
                            type="button"
                            onClick={() => toggleMode("register")}
                            className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                                mode === "register"
                                    ? "bg-blue-600 text-white"
                                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                            }`}
                        >
                            Register
                        </button>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                            Email
                        </label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            required
                            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                            Password
                        </label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            required
                            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    {error && (
                        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-100">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-600/30 transition-colors hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? "Working..." : submitLabel}
                    </button>
                </form>

                <p className="mt-6 text-center text-sm text-slate-400">
                    {mode === "login" ? "Don’t have an account?" : "Already have an account?"}{" "}
                    <button
                        type="button"
                        className="text-blue-400 hover:text-blue-300 underline underline-offset-4"
                        onClick={() => toggleMode(mode === "login" ? "register" : "login")}
                    >
                        {mode === "login" ? "Register instead" : "Login instead"}
                    </button>
                </p>
            </div>
        </main>
    );
}
