"use client";

import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";
import type { KeycloakTokenParsed } from "keycloak-js";
import { getKeycloak, initKeycloak } from "@/lib/keycloak";

type KeycloakAuthState = {
    isInitialised: boolean;
    isAuthenticated: boolean;
    token: string | null;
    email: string | null;
    username: string | null;
    login: () => Promise<void>;
    register: () => Promise<void>;
    logout: () => Promise<void>;
};

const AuthContext = createContext<KeycloakAuthState | null>(null);

type ProvidersProps = {
    children: ReactNode;
};

function tokenEmail(tokenParsed: KeycloakTokenParsed | undefined): string | null {
    const email = (tokenParsed as Record<string, unknown> | undefined)?.email;
    return typeof email === "string" ? email : null;
}

function tokenUsername(tokenParsed: KeycloakTokenParsed | undefined): string | null {
    const preferred = (tokenParsed as Record<string, unknown> | undefined)?.preferred_username;
    if (typeof preferred === "string" && preferred.length > 0) return preferred;
    const fallback = (tokenParsed as Record<string, unknown> | undefined)?.name;
    return typeof fallback === "string" ? fallback : null;
}

export default function Providers({ children }: ProvidersProps): JSX.Element {
    const [isInitialised, setIsInitialised] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [token, setToken] = useState<string | null>(null);
    const [email, setEmail] = useState<string | null>(null);
    const [username, setUsername] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        const keycloak = getKeycloak();

        const sync = () => {
            if (cancelled) return;
            setIsAuthenticated(Boolean(keycloak.authenticated));
            setToken(keycloak.token ?? null);
            setEmail(tokenEmail(keycloak.tokenParsed));
            setUsername(tokenUsername(keycloak.tokenParsed));
        };

        const init = async () => {
            try {
                await initKeycloak({
                    onLoad: "check-sso",
                    pkceMethod: "S256",
                    checkLoginIframe: false,
                    silentCheckSsoRedirectUri:
                        typeof window !== "undefined"
                            ? `${window.location.origin}/silent-check-sso.html`
                            : undefined
                });
            } finally {
                if (cancelled) return;
                setIsInitialised(true);
                sync();
            }
        };

        void init();

        const refresh = window.setInterval(() => {
            if (!keycloak.authenticated) return;
            void keycloak
                .updateToken(60)
                .then(() => sync())
                .catch(() => {
                    // Token refresh failed; treat as signed out.
                    sync();
                });
        }, 30_000);

        return () => {
            cancelled = true;
            window.clearInterval(refresh);
        };
    }, []);

    const value = useMemo<KeycloakAuthState>(() => {
        const keycloak = getKeycloak();
        return {
            isInitialised,
            isAuthenticated,
            token,
            email,
            username,
            login: async () => {
                await keycloak.login({ redirectUri: `${window.location.origin}/` });
            },
            register: async () => {
                await keycloak.register({ redirectUri: `${window.location.origin}/` });
            },
            logout: async () => {
                await keycloak.logout({ redirectUri: `${window.location.origin}/auth` });
            }
        };
    }, [email, isAuthenticated, isInitialised, token, username]);

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): KeycloakAuthState {
    const ctx = useContext(AuthContext);
    if (!ctx) {
        throw new Error("useAuth must be used within <Providers />");
    }
    return ctx;
}
