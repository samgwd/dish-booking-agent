"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/providers";

export default function AuthPage(): JSX.Element {
    const router = useRouter();
    const { isInitialised, isAuthenticated, login, register } = useAuth();

    useEffect(() => {
        if (!isInitialised) return;
        if (isAuthenticated) {
            router.replace("/");
        }
    }, [isAuthenticated, isInitialised, router]);

    return (
        <main className="min-h-screen w-full bg-slate-950 text-white flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-2xl">
                <div className="flex justify-between items-center mb-6 gap-4">
                    <div>
                        <p className="text-sm text-slate-400">Room Booking Agent</p>
                        <h1 className="text-2xl font-semibold">Welcome back</h1>
                    </div>
                </div>

                <p className="text-sm text-slate-300 mb-6">
                    Sign in to your account.
                </p>

                <div className="flex flex-col gap-3">
                    <button
                        type="button"
                        disabled={!isInitialised}
                        onClick={() => void login()}
                        className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-600/30 transition-colors hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        {!isInitialised ? "Loading..." : "Sign in"}
                    </button>

                    <button
                        type="button"
                        disabled={!isInitialised}
                        onClick={() => void register()}
                        className="w-full rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-slate-700 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        Create an account
                    </button>
                </div>
            </div>
        </main>
    );
}
