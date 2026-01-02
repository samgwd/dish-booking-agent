"use client";

import { useState } from "react";
import Link from "next/link";
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
                <Link
                    href="/settings"
                    className="rounded-md bg-slate-800 p-1.5 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                    aria-label="Settings"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        className="w-4 h-4"
                    >
                        <path
                            fillRule="evenodd"
                            d="M7.84 1.804A1 1 0 018.82 1h2.36a1 1 0 01.98.804l.331 1.652a6.993 6.993 0 011.929 1.115l1.598-.54a1 1 0 011.186.447l1.18 2.044a1 1 0 01-.205 1.251l-1.267 1.113a7.047 7.047 0 010 2.228l1.267 1.113a1 1 0 01.206 1.25l-1.18 2.045a1 1 0 01-1.187.447l-1.598-.54a6.993 6.993 0 01-1.929 1.115l-.33 1.652a1 1 0 01-.98.804H8.82a1 1 0 01-.98-.804l-.331-1.652a6.993 6.993 0 01-1.929-1.115l-1.598.54a1 1 0 01-1.186-.447l-1.18-2.044a1 1 0 01.205-1.251l1.267-1.114a7.05 7.05 0 010-2.227L1.821 7.773a1 1 0 01-.206-1.25l1.18-2.045a1 1 0 011.187-.447l1.598.54A6.993 6.993 0 017.51 3.456l.33-1.652zM10 13a3 3 0 100-6 3 3 0 000 6z"
                            clipRule="evenodd"
                        />
                    </svg>
                </Link>
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
