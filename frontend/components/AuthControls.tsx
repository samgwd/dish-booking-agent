"use client";

import { useState } from "react";
import { useAuth } from "@/app/providers";

type AuthControlsProps = {
    className?: string;
};

export default function AuthControls({ className }: AuthControlsProps): JSX.Element | null {
    const { isInitialised, isAuthenticated, email, username, logout } = useAuth();
    const [isProcessing, setIsProcessing] = useState<"logout" | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleLogout = async (): Promise<void> => {
        setIsProcessing("logout");
        setError(null);

        try {
            await logout();
        } catch (actionError) {
            console.error(actionError);
            setError("Failed to sign out. Please try again.");
        } finally {
            setIsProcessing(null);
        }
    };

    if (!isInitialised || !isAuthenticated) return null;

    return (
        <div className={`flex flex-col gap-2 items-end ${className ?? ""}`}>
            <span className="text-xs text-slate-300">
                Signed in as {email ?? username ?? "unknown"}
            </span>
            {error && (
                <div className="rounded-md bg-red-500/10 border border-red-500/40 px-2 py-1 text-xs text-red-100">
                    {error}
                </div>
            )}
            <div className="flex gap-2">
                <button
                    type="button"
                    onClick={() => void handleLogout()}
                    disabled={isProcessing !== null}
                    className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                    {isProcessing === "logout" ? "Logging out..." : "Logout"}
                </button>
            </div>
        </div>
    );
}
