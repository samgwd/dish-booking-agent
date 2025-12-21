"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/app/providers";
import {
    getAllSecrets,
    setSecret,
    deleteSecret,
    initiateGoogleOAuth,
    getGoogleOAuthStatus,
    disconnectGoogleOAuth,
} from "@/lib/secrets";
import "./settings.css";

const DISH_CREDENTIAL_KEYS = ["DISH_COOKIE", "TEAM_ID", "MEMBER_ID"] as const;
type DishCredentialKey = (typeof DISH_CREDENTIAL_KEYS)[number];

const GCAL_CREDENTIAL_KEYS = [
    "GOOGLE_CALENDAR_ACCESS_TOKEN",
    "GOOGLE_CALENDAR_REFRESH_TOKEN",
    "GOOGLE_CALENDAR_EXPIRY_DATE",
] as const;
type GCalCredentialKey = (typeof GCAL_CREDENTIAL_KEYS)[number];

type CredentialKey = DishCredentialKey | GCalCredentialKey;
const ALL_CREDENTIAL_KEYS = [...DISH_CREDENTIAL_KEYS, ...GCAL_CREDENTIAL_KEYS] as const;

type CredentialInfo = {
    label: string;
    description: string;
    placeholder: string;
};

const DISH_CREDENTIAL_INFO: Record<DishCredentialKey, CredentialInfo> = {
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

const GCAL_CREDENTIAL_INFO: Record<GCalCredentialKey, CredentialInfo> = {
    GOOGLE_CALENDAR_ACCESS_TOKEN: {
        label: "Access Token",
        description: "OAuth access token from Google",
        placeholder: "ya29.a0...",
    },
    GOOGLE_CALENDAR_REFRESH_TOKEN: {
        label: "Refresh Token",
        description: "OAuth refresh token for automatic renewal",
        placeholder: "1//0...",
    },
    GOOGLE_CALENDAR_EXPIRY_DATE: {
        label: "Expiry Date",
        description: "Token expiry as Unix timestamp in milliseconds",
        placeholder: "e.g. 1703980800000",
    },
};

type CredentialState = {
    value: string;
    originalValue: string | null;
    isVisible: boolean;
    isSaving: boolean;
    saveStatus: "idle" | "saved" | "error";
};

function EyeIcon(): JSX.Element {
    return (
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
    );
}

function EyeSlashIcon(): JSX.Element {
    return (
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
    );
}

function SpinnerIcon(): JSX.Element {
    return (
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
    );
}

function LoadingSpinner(): JSX.Element {
    return (
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
    );
}

type CredentialFieldProps = {
    credKey: CredentialKey;
    info: CredentialInfo;
    state: CredentialState;
    hasChanges: boolean;
    onInputChange: (key: CredentialKey, value: string) => void;
    onToggleVisibility: (key: CredentialKey) => void;
    onSave: (key: CredentialKey) => void;
};

function CredentialField({
    credKey,
    info,
    state,
    hasChanges,
    onInputChange,
    onToggleVisibility,
    onSave,
}: CredentialFieldProps): JSX.Element {
    return (
        <div className="credential-field">
            <label
                htmlFor={credKey}
                className="block text-sm font-medium text-slate-200 mb-1"
            >
                {info.label}
            </label>
            <p className="text-xs text-slate-500 mb-2">{info.description}</p>
            <div className="flex gap-2">
                <div className="relative flex-1">
                    <input
                        id={credKey}
                        type={state.isVisible ? "text" : "password"}
                        value={state.value}
                        onChange={(e) => onInputChange(credKey, e.target.value)}
                        placeholder={info.placeholder}
                        className="settings-input w-full rounded-lg px-4 py-2.5 pr-10 text-sm text-white placeholder-slate-500"
                    />
                    <button
                        type="button"
                        onClick={() => onToggleVisibility(credKey)}
                        className="visibility-toggle absolute right-3 top-1/2 -translate-y-1/2 text-slate-500"
                        aria-label={state.isVisible ? "Hide value" : "Show value"}
                    >
                        {state.isVisible ? <EyeSlashIcon /> : <EyeIcon />}
                    </button>
                </div>
                <button
                    type="button"
                    onClick={() => onSave(credKey)}
                    disabled={!hasChanges || state.isSaving}
                    className="save-button rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-indigo-600"
                >
                    {state.isSaving ? <SpinnerIcon /> : "Save"}
                </button>
            </div>
            {/* Status indicator */}
            {state.saveStatus === "saved" && (
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
            {state.saveStatus === "error" && (
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
}

export default function SettingsPage(): JSX.Element {
    const router = useRouter();
    const { isInitialised, isAuthenticated, token } = useAuth();
    const [isReady, setIsReady] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isGoogleConnected, setIsGoogleConnected] = useState(false);
    const [isGoogleLoading, setIsGoogleLoading] = useState(false);
    const [showAdvancedGcal, setShowAdvancedGcal] = useState(false);

    const [credentials, setCredentials] = useState<Record<CredentialKey, CredentialState>>(() => {
        const initial: Record<string, CredentialState> = {};
        for (const key of ALL_CREDENTIAL_KEYS) {
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

    // Load existing secrets and Google OAuth status
    const loadSecrets = useCallback(async () => {
        if (!token) return;
        setIsLoading(true);
        setError(null);

        try {
            // Load secrets and Google OAuth status in parallel
            const [secrets, googleStatus] = await Promise.all([
                getAllSecrets(token, [...ALL_CREDENTIAL_KEYS]),
                getGoogleOAuthStatus(token).catch(() => false),
            ]);

            setIsGoogleConnected(googleStatus);

            setCredentials((prev) => {
                const updated = { ...prev };
                for (const key of ALL_CREDENTIAL_KEYS) {
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

    // Handle Google OAuth connect
    const handleGoogleConnect = async (): Promise<void> => {
        if (!token) return;
        setIsGoogleLoading(true);
        setError(null);

        try {
            await initiateGoogleOAuth(token);
            // User will be redirected to Google, so this won't complete
        } catch (err) {
            console.error("Failed to initiate Google OAuth:", err);
            setError("Failed to start Google Calendar connection. Please try again.");
            setIsGoogleLoading(false);
        }
    };

    // Handle Google OAuth disconnect
    const handleGoogleDisconnect = async (): Promise<void> => {
        if (!token) return;
        setIsGoogleLoading(true);
        setError(null);

        try {
            await disconnectGoogleOAuth(token);
            setIsGoogleConnected(false);
            // Clear the credential values in the UI
            setCredentials((prev) => {
                const updated = { ...prev };
                for (const key of GCAL_CREDENTIAL_KEYS) {
                    updated[key] = {
                        ...updated[key],
                        value: "",
                        originalValue: null,
                    };
                }
                return updated;
            });
        } catch (err) {
            console.error("Failed to disconnect Google Calendar:", err);
            setError("Failed to disconnect Google Calendar. Please try again.");
        } finally {
            setIsGoogleLoading(false);
        }
    };

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
                        Configure your credentials for DiSH and Google Calendar
                    </p>
                </header>

                {/* Error banner */}
                {error && (
                    <div className="mb-6 rounded-lg bg-red-900/40 border border-red-500/40 px-4 py-3 text-sm text-red-100">
                        {error}
                    </div>
                )}

                {/* DiSH Credentials card */}
                <div className="settings-card rounded-2xl p-6 md:p-8 mb-6">
                    <h2 className="text-lg font-semibold text-white mb-1">DiSH Credentials</h2>
                    <p className="text-sm text-slate-400 mb-6">
                        These credentials are required for the booking agent to interact with DiSH
                        on your behalf. Use the{" "}
                        <code className="text-indigo-400 bg-indigo-950/50 px-1.5 py-0.5 rounded text-xs">
                            dish-setup
                        </code>{" "}
                        CLI tool to retrieve them.
                    </p>

                    {isLoading ? (
                        <LoadingSpinner />
                    ) : (
                        <div className="space-y-6">
                            {DISH_CREDENTIAL_KEYS.map((key) => (
                                <CredentialField
                                    key={key}
                                    credKey={key}
                                    info={DISH_CREDENTIAL_INFO[key]}
                                    state={credentials[key]}
                                    hasChanges={hasChanges(key)}
                                    onInputChange={handleInputChange}
                                    onToggleVisibility={toggleVisibility}
                                    onSave={(k) => void handleSave(k)}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {/* Google Calendar Credentials card */}
                <div className="settings-card rounded-2xl p-6 md:p-8">
                    <h2 className="text-lg font-semibold text-white mb-1">
                        Google Calendar
                    </h2>
                    <p className="text-sm text-slate-400 mb-6">
                        Connect your Google Calendar account to enable calendar integration.
                    </p>

                    {isLoading ? (
                        <LoadingSpinner />
                    ) : isGoogleConnected ? (
                        <>
                            {/* Connected status */}
                            <div className="mb-6 p-4 bg-emerald-950/30 border border-emerald-800/50 rounded-lg">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-emerald-400">
                                        <svg
                                            className="w-5 h-5"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                        <span className="font-medium">Google Calendar Connected</span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => void handleGoogleDisconnect()}
                                        disabled={isGoogleLoading}
                                        className="text-sm text-slate-400 hover:text-red-400 transition-colors disabled:opacity-50"
                                    >
                                        {isGoogleLoading ? "Disconnecting..." : "Disconnect"}
                                    </button>
                                </div>
                            </div>

                            {/* Advanced: Manual token management */}
                            <div className="border-t border-slate-700/50 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowAdvancedGcal(!showAdvancedGcal)}
                                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-300 transition-colors"
                                >
                                    <svg
                                        className={`w-4 h-4 transition-transform ${showAdvancedGcal ? "rotate-90" : ""}`}
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                    >
                                        <path
                                            fillRule="evenodd"
                                            d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                                            clipRule="evenodd"
                                        />
                                    </svg>
                                    Advanced: Manual Token Management
                                </button>

                                {showAdvancedGcal && (
                                    <div className="mt-4 space-y-6">
                                        {GCAL_CREDENTIAL_KEYS.map((key) => (
                                            <CredentialField
                                                key={key}
                                                credKey={key}
                                                info={GCAL_CREDENTIAL_INFO[key]}
                                                state={credentials[key]}
                                                hasChanges={hasChanges(key)}
                                                onInputChange={handleInputChange}
                                                onToggleVisibility={toggleVisibility}
                                                onSave={(k) => void handleSave(k)}
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div>
                            <button
                                type="button"
                                onClick={() => void handleGoogleConnect()}
                                disabled={isGoogleLoading}
                                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isGoogleLoading ? (
                                    <SpinnerIcon />
                                ) : (
                                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                                        <path
                                            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                            fill="#4285F4"
                                        />
                                        <path
                                            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                            fill="#34A853"
                                        />
                                        <path
                                            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                            fill="#FBBC05"
                                        />
                                        <path
                                            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                            fill="#EA4335"
                                        />
                                    </svg>
                                )}
                                Connect Google Calendar
                            </button>
                            <p className="mt-3 text-xs text-slate-500">
                                You&apos;ll be redirected to Google to authorise access to your calendar.
                            </p>
                        </div>
                    )}
                </div>

                {/* Help section */}
                <div className="mt-8 text-center">
                    <p className="text-sm text-slate-500">
                        Need help getting your credentials?{" "}
                        <a
                            href="https://github.com/samgwd/dish-booking-agent#readme"
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
