"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/app/providers";
import { getAllSecrets, setSecret, deleteSecret } from "@/lib/secrets";
import "./settings.css";

const CREDENTIAL_KEYS = ["DISH_COOKIE", "TEAM_ID", "MEMBER_ID"] as const;
type CredentialKey = (typeof CREDENTIAL_KEYS)[number];

const CREDENTIAL_INFO: Record<CredentialKey, { label: string; description: string; placeholder: string }> = {
    DISH_COOKIE: {
        label: "DiSH Cookie",
        description: "Your session cookie from Dish (connect.sid=...)",
        placeholder: "connect.sid=s%3A...",
    },
    TEAM_ID: {
        label: "Team ID",
        description: "Your Dish team identifier",
        placeholder: "e.g. 5f1234567890abcdef123456",
    },
    MEMBER_ID: {
        label: "Member ID",
        description: "Your Dish member identifier",
        placeholder: "e.g. 5f1234567890abcdef654321",
    },
};

type CredentialState = {
    value: string;
    originalValue: string | null;
    isVisible: boolean;
    isSaving: boolean;
    saveStatus: "idle" | "saved" | "error";
};

export default function SettingsPage(): JSX.Element {
    const router = useRouter();
    const { isInitialised, isAuthenticated, token } = useAuth();
    const [isReady, setIsReady] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [credentials, setCredentials] = useState<Record<CredentialKey, CredentialState>>(() => {
        const initial: Record<string, CredentialState> = {};
        for (const key of CREDENTIAL_KEYS) {
            initial[key] = {
                value: "",
                originalValue: null,
                isVisible: false,
                isSaving: false,
                saveStatus: "idle",
            };
        }
        return initial as Record<CredentialKey, CredentialState>;
    });

    // Redirect if not authenticated
    useEffect(() => {
        if (!isInitialised) return;
        if (!isAuthenticated) {
            router.replace("/auth");
            return;
        }
        setIsReady(true);
    }, [isAuthenticated, isInitialised, router]);

    // Apply page styling
    useEffect(() => {
        if (!isReady) return;
        document.documentElement.classList.add("dark");
        document.body.classList.add("settings-page-body", "text-white", "font-display");
        return () => {
            document.documentElement.classList.remove("dark");
            document.body.classList.remove("settings-page-body", "text-white", "font-display");
        };
    }, [isReady]);

    // Load existing secrets
    const loadSecrets = useCallback(async () => {
        if (!token) return;
        setIsLoading(true);
        setError(null);

        try {
            const secrets = await getAllSecrets(token, [...CREDENTIAL_KEYS]);
            setCredentials((prev) => {
                const updated = { ...prev };
                for (const key of CREDENTIAL_KEYS) {
                    const value = secrets[key];
                    updated[key] = {
                        ...updated[key],
                        value: value ?? "",
                        originalValue: value,
                    };
                }
                return updated;
            });
        } catch (err) {
            console.error("Failed to load secrets:", err);
            setError("Failed to load your credentials. Please try again.");
        } finally {
            setIsLoading(false);
        }
    }, [token]);

    useEffect(() => {
        if (isReady && token) {
            void loadSecrets();
        }
    }, [isReady, token, loadSecrets]);

    const handleInputChange = (key: CredentialKey, value: string): void => {
        setCredentials((prev) => ({
            ...prev,
            [key]: {
                ...prev[key],
                value,
                saveStatus: "idle",
            },
        }));
    };

    const toggleVisibility = (key: CredentialKey): void => {
        setCredentials((prev) => ({
            ...prev,
            [key]: {
                ...prev[key],
                isVisible: !prev[key].isVisible,
            },
        }));
    };

    const handleSave = async (key: CredentialKey): Promise<void> => {
        if (!token) return;

        const cred = credentials[key];
        const trimmedValue = cred.value.trim();

        setCredentials((prev) => ({
            ...prev,
            [key]: { ...prev[key], isSaving: true, saveStatus: "idle" },
        }));

        try {
            if (trimmedValue === "") {
                await deleteSecret(token, key);
            } else {
                await setSecret(token, key, trimmedValue);
            }

            setCredentials((prev) => ({
                ...prev,
                [key]: {
                    ...prev[key],
                    value: trimmedValue,
                    originalValue: trimmedValue === "" ? null : trimmedValue,
                    isSaving: false,
                    saveStatus: "saved",
                },
            }));

            setTimeout(() => {
                setCredentials((prev) => ({
                    ...prev,
                    [key]: { ...prev[key], saveStatus: "idle" },
                }));
            }, 2000);
        } catch (err) {
            console.error(`Failed to save ${key}:`, err);
            setCredentials((prev) => ({
                ...prev,
                [key]: { ...prev[key], isSaving: false, saveStatus: "error" },
            }));
        }
    };

    const hasChanges = (key: CredentialKey): boolean => {
        const cred = credentials[key];
        const currentValue = cred.value.trim();
        const originalValue = cred.originalValue ?? "";
        return currentValue !== originalValue;
    };

    if (!isReady) {
        return <></>;
    }

    return (
        <main className="relative flex flex-col items-center min-h-screen w-full p-6 md:p-10">
            {/* Back navigation */}
            <div className="absolute top-4 left-4">
                <Link
                    href="/"
                    className="inline-flex items-center gap-2 rounded-lg bg-slate-800/60 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700/60 hover:text-white transition-colors"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        className="w-4 h-4"
                    >
                        <path
                            fillRule="evenodd"
                            d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z"
                            clipRule="evenodd"
                        />
                    </svg>
                    Back
                </Link>
            </div>

            <div className="w-full max-w-2xl mt-16">
                {/* Header */}
                <header className="text-center mb-10">
                    <h1 className="text-3xl md:text-4xl font-bold text-white tracking-wide">
                        Settings
                    </h1>
                    <p className="text-slate-400 mt-2 text-base">
                        Configure your DiSH booking credentials
                    </p>
                </header>

                {/* Error banner */}
                {error && (
                    <div className="mb-6 rounded-lg bg-red-900/40 border border-red-500/40 px-4 py-3 text-sm text-red-100">
                        {error}
                    </div>
                )}

                {/* Credentials card */}
                <div className="settings-card rounded-2xl p-6 md:p-8">
                    <h2 className="text-lg font-semibold text-white mb-1">DiSH Credentials</h2>
                    <p className="text-sm text-slate-400 mb-6">
                        These credentials are required for the booking agent to interact with Dish on your behalf.
                        Use the{" "}
                        <code className="text-indigo-400 bg-indigo-950/50 px-1.5 py-0.5 rounded text-xs">
                            dish-setup
                        </code>{" "}
                        CLI tool to retrieve them.
                    </p>

                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="flex items-center gap-3 text-slate-400">
                                <svg
                                    className="animate-spin h-5 w-5"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                >
                                    <circle
                                        className="opacity-25"
                                        cx="12"
                                        cy="12"
                                        r="10"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                    />
                                    <path
                                        className="opacity-75"
                                        fill="currentColor"
                                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                    />
                                </svg>
                                <span>Loading credentials...</span>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {CREDENTIAL_KEYS.map((key) => {
                                const info = CREDENTIAL_INFO[key];
                                const cred = credentials[key];
                                const changed = hasChanges(key);

                                return (
                                    <div key={key} className="credential-field">
                                        <label
                                            htmlFor={key}
                                            className="block text-sm font-medium text-slate-200 mb-1"
                                        >
                                            {info.label}
                                        </label>
                                        <p className="text-xs text-slate-500 mb-2">
                                            {info.description}
                                        </p>
                                        <div className="flex gap-2">
                                            <div className="relative flex-1">
                                                <input
                                                    id={key}
                                                    type={cred.isVisible ? "text" : "password"}
                                                    value={cred.value}
                                                    onChange={(e) => handleInputChange(key, e.target.value)}
                                                    placeholder={info.placeholder}
                                                    className="settings-input w-full rounded-lg px-4 py-2.5 pr-10 text-sm text-white placeholder-slate-500"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => toggleVisibility(key)}
                                                    className="visibility-toggle absolute right-3 top-1/2 -translate-y-1/2 text-slate-500"
                                                    aria-label={cred.isVisible ? "Hide value" : "Show value"}
                                                >
                                                    {cred.isVisible ? (
                                                        <svg
                                                            xmlns="http://www.w3.org/2000/svg"
                                                            viewBox="0 0 20 20"
                                                            fill="currentColor"
                                                            className="w-4 h-4"
                                                        >
                                                            <path
                                                                fillRule="evenodd"
                                                                d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.745-1.745a10.029 10.029 0 003.3-4.38 1.651 1.651 0 000-1.185A10.004 10.004 0 009.999 3a9.956 9.956 0 00-4.744 1.194L3.28 2.22zM7.752 6.69l1.092 1.092a2.5 2.5 0 013.374 3.373l1.091 1.092a4 4 0 00-5.557-5.557z"
                                                                clipRule="evenodd"
                                                            />
                                                            <path d="M10.748 13.93l2.523 2.523a9.987 9.987 0 01-3.27.547c-4.258 0-7.894-2.66-9.337-6.41a1.651 1.651 0 010-1.186A10.007 10.007 0 012.839 6.02L6.07 9.252a4 4 0 004.678 4.678z" />
                                                        </svg>
                                                    ) : (
                                                        <svg
                                                            xmlns="http://www.w3.org/2000/svg"
                                                            viewBox="0 0 20 20"
                                                            fill="currentColor"
                                                            className="w-4 h-4"
                                                        >
                                                            <path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" />
                                                            <path
                                                                fillRule="evenodd"
                                                                d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                                                                clipRule="evenodd"
                                                            />
                                                        </svg>
                                                    )}
                                                </button>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => void handleSave(key)}
                                                disabled={!changed || cred.isSaving}
                                                className="save-button rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-indigo-600"
                                            >
                                                {cred.isSaving ? (
                                                    <svg
                                                        className="animate-spin h-4 w-4"
                                                        xmlns="http://www.w3.org/2000/svg"
                                                        fill="none"
                                                        viewBox="0 0 24 24"
                                                    >
                                                        <circle
                                                            className="opacity-25"
                                                            cx="12"
                                                            cy="12"
                                                            r="10"
                                                            stroke="currentColor"
                                                            strokeWidth="4"
                                                        />
                                                        <path
                                                            className="opacity-75"
                                                            fill="currentColor"
                                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                                        />
                                                    </svg>
                                                ) : (
                                                    "Save"
                                                )}
                                            </button>
                                        </div>
                                        {/* Status indicator */}
                                        {cred.saveStatus === "saved" && (
                                            <p className="status-saved mt-2 text-xs text-emerald-400 flex items-center gap-1">
                                                <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    viewBox="0 0 16 16"
                                                    fill="currentColor"
                                                    className="w-3.5 h-3.5"
                                                >
                                                    <path
                                                        fillRule="evenodd"
                                                        d="M12.416 3.376a.75.75 0 01.208 1.04l-5 7.5a.75.75 0 01-1.154.114l-3-3a.75.75 0 011.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 011.04-.207z"
                                                        clipRule="evenodd"
                                                    />
                                                </svg>
                                                Saved successfully
                                            </p>
                                        )}
                                        {cred.saveStatus === "error" && (
                                            <p className="mt-2 text-xs text-red-400 flex items-center gap-1">
                                                <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    viewBox="0 0 16 16"
                                                    fill="currentColor"
                                                    className="w-3.5 h-3.5"
                                                >
                                                    <path
                                                        fillRule="evenodd"
                                                        d="M8 15A7 7 0 108 1a7 7 0 000 14zM8 4a.75.75 0 01.75.75v3a.75.75 0 01-1.5 0v-3A.75.75 0 018 4zm0 8a1 1 0 100-2 1 1 0 000 2z"
                                                        clipRule="evenodd"
                                                    />
                                                </svg>
                                                Failed to save. Please try again.
                                            </p>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Help section */}
                <div className="mt-8 text-center">
                    <p className="text-sm text-slate-500">
                        Need help getting your credentials?{" "}
                        <a
                            href="https://github.com/samgwd/dish-booking-agent/tree/main/credential-cli#readme"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-400 hover:text-indigo-300 underline"
                        >
                            View the setup guide
                        </a>
                    </p>
                </div>
            </div>
        </main>
    );
}
