"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiBase } from "@/lib/apiBase";
import { clearStoredAuth, getStoredAuth } from "@/lib/authStorage";

type Action = "logout" | "delete";

type AuthControlsProps = {
    className?: string;
};

export default function AuthControls({ className }: AuthControlsProps): JSX.Element | null {
    const [userId, setUserId] = useState<string | null>(null);
    const [email, setEmail] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState<Action | null>(null);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    useEffect(() => {
        const stored = getStoredAuth();
        setUserId(stored.userId);
        setEmail(stored.email);
    }, []);

    const handleAction = async (action: Action): Promise<void> => {
        const currentUserId = userId ?? getStoredAuth().userId;
        if (!currentUserId) {
            clearStoredAuth();
            router.replace("/auth");
            return;
        }

        setIsProcessing(action);
        setError(null);

        try {
            const response = await fetch(`${apiBase}${action === "logout" ? "/logout" : "/delete-user"}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: currentUserId })
            });

            if (response.status === 404) {
                clearStoredAuth();
                router.replace("/auth");
                return;
            }

            if (!response.ok) {
                setError(
                    action === "logout"
                        ? "Failed to log out. Please try again."
                        : "Unable to delete account right now."
                );
                return;
            }

            clearStoredAuth();
            router.replace("/auth");
        } catch (actionError) {
            console.error(actionError);
            setError("Unable to reach the server. Please try again.");
        } finally {
            setIsProcessing(null);
        }
    };

    if (!userId) return null;

    return (
        <div className={`flex flex-col gap-2 items-end ${className ?? ""}`}>
            {email && <span className="text-xs text-slate-300">Signed in as {email}</span>}
            {error && (
                <div className="rounded-md bg-red-500/10 border border-red-500/40 px-2 py-1 text-xs text-red-100">
                    {error}
                </div>
            )}
            <div className="flex gap-2">
                <button
                    type="button"
                    onClick={() => void handleAction("logout")}
                    disabled={isProcessing !== null}
                    className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                    {isProcessing === "logout" ? "Logging out..." : "Logout"}
                </button>
                <button
                    type="button"
                    onClick={() => void handleAction("delete")}
                    disabled={isProcessing !== null}
                    className="rounded-md border border-red-500/60 px-3 py-1.5 text-xs font-semibold text-red-100 hover:bg-red-500/10 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                    {isProcessing === "delete" ? "Deleting..." : "Delete account"}
                </button>
            </div>
        </div>
    );
}
