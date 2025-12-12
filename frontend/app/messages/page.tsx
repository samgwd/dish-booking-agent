"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AuthControls from "@/components/AuthControls";
import ChatInput from "@/components/ChatInput";
import Message, { type MessageProps } from "@/components/Message";
import { apiBase } from "@/lib/apiBase";
import { getStoredAuth } from "@/lib/authStorage";
const storageKey = "chatMessages";
const signatureOf = (message: MessageProps): string =>
    `${message.author}|${message.isUser ? "user" : "assistant"}|${message.content}`;

const userAvatar =
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDjK9X3BZOWoc9jiC5v0rOYSnRJdYSxF53hzeB9iyHyFxtdeoKH-9f81MD9GKb5MCwlx14xjpOOdJkv5zYwW8jipICJ2s9GzLA9BZCQFJFymZoDsNTgRrH5fEu4U1l3vxB7E2ehg0pLfA4iymFOLLPvotA331oedtMqsXJ5QnFG8OzxTWl5wabg6T3g7Ke2RmSQgbFViXTQBbCqWQhzZRb4l2pRJhA3jM0wn7puCca_HktpdYFcv0r9RUYpuh9NLBQ1ufxZhrhE9Eo";

const assistantAvatar =
    "https://lh3.googleusercontent.com/aida-public/AB6AXuA1ORR1W1DJE0Mb41HZ2PPHaBJZsPGwKvhCmpWozZrvjBKIx_pfSQtlelyJFaiqAb_0HehE39oTKpqwGlLM2jICKKaCCd1g_qrYKdNCMROEz9rSEl8ofNfoRxf5m7T3DI1-QXhVM7OCeS9uVkBBnOPDftNwfSftgjab9el9n3G_QMojwKzEIsmOoTAoSgWuUTJkvJr5CuQbY6dM5IJvk2fFl04Wy_sNbktQR-8q7-sQFfQ4gpCW6BbWAXsxb22-dSoeXnbB9i3a9Ks";

/** Chat transcript page that renders messages, handles sending, and syncs state to storage. */
export default function MessagePage(): JSX.Element {
    const router = useRouter();
    const [isReady, setIsReady] = useState(false);
    const [messages, setMessages] = useState<MessageProps[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [isSending, setIsSending] = useState<boolean>(false);
    const processedInitialMessage = useRef<boolean>(false);
    const sessionIdRef = useRef<string | null>(null);
    const bottomRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const stored = getStoredAuth();
        if (!stored.userId) {
            router.replace("/auth");
            return;
        }
        setIsReady(true);
    }, [router]);

    /** Ensure a stable session id exists and store it for reuse. */
    const ensureSessionId = useCallback((): string => {
        if (sessionIdRef.current) return sessionIdRef.current;

        const createdId =
            typeof crypto !== "undefined" && "randomUUID" in crypto
                ? crypto.randomUUID()
                : `session-${Date.now()}`;

        sessionIdRef.current = createdId;
        try {
            sessionStorage.setItem("chatSessionId", createdId);
        } catch {
            // Session storage may be unavailable in some environments.
        }

        return createdId;
    }, []);

    /** Restore an existing session id from storage or create one once on mount. */
    useEffect(() => {
        if (!isReady || sessionIdRef.current) return;
        try {
            const storedId = sessionStorage.getItem("chatSessionId");
            if (storedId) {
                sessionIdRef.current = storedId;
                return;
            }
        } catch {
            // Continue with a generated session id if storage fails.
        }
        ensureSessionId();
    }, [ensureSessionId, isReady]);

    /** Send a user message to the backend, append responses, and handle transient errors. */
    const handleSend = useCallback(
        async (content: string) => {
            setError(null);

            const timeStamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            const userMessage: MessageProps = {
                author: "You",
                time: timeStamp,
                content,
                isUser: true,
                avatarUrl: userAvatar
            };

            setMessages((prev) => [...prev, userMessage]);
            setIsSending(true);


            try {
                const sessionId = ensureSessionId();
                const url = `${apiBase}/send-message?${new URLSearchParams({
                    message: content,
                    session: sessionId
                }).toString()}`;

                const response = await fetch(url, { method: "GET" });

                if (!response.ok) {
                    throw new Error(`Request failed with status ${response.status}`);
                }

                const payload = await response.json();
                if (!Array.isArray(payload)) {
                    throw new Error("Unexpected response shape");
                }

                const replyTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

                setMessages((prev) => {
                    const nextMessages = payload
                        .map((text) => ({
                            author: "AI Assistant",
                            time: replyTime,
                            content: text,
                            isUser: false,
                            avatarUrl: assistantAvatar
                        }))
                    return [...prev, ...nextMessages];
                });
            } catch (fetchError) {
                console.error(fetchError);
                setError("Unable to reach the booking service. Please try again.");
            } finally {
                setIsSending(false);
            }
        },
        [ensureSessionId]
    );

    /** Apply chat page theming on mount and tidy up on unmount. */
    useEffect(() => {
        if (!isReady) return;
        document.documentElement.classList.add("dark");
        document.body.classList.add("chat-page-body", "font-display");
        return () => {
            document.documentElement.classList.remove("dark");
            document.body.classList.remove("chat-page-body", "font-display");
        };
    }, [isReady]);


    /** Send a pre-seeded initial message (if any) only once per session. */
    useEffect(() => {
        if (!isReady || processedInitialMessage.current) return;

        try {
            const incomingMessage = sessionStorage.getItem("initialMessage");
            if (!incomingMessage) return;

            processedInitialMessage.current = true;
            sessionStorage.removeItem("initialMessage");
            void handleSend(incomingMessage);
        } catch {
            // If storage is unavailable, simply render without a pre-seeded message.
        }
    }, [handleSend, isReady]);

    /** Reset conversation state and clear stored session data. */
    const handleReset = (): void => {
        setMessages([]);
        processedInitialMessage.current = false;
        try {
            sessionStorage.removeItem(storageKey);
            sessionStorage.removeItem("chatSessionId");
        } catch {
            // Session storage may be unavailable; safe to ignore.
        }
        sessionIdRef.current = null;
        ensureSessionId();
    };

    /** Keep the latest message in view whenever messages change. */
    useEffect(() => {
        if (!isReady) return;
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isReady]);

    if (!isReady) {
        return null;
    }

    return (
        <div className="relative flex h-screen w-full flex-row overflow-hidden">
            <main className="flex h-full flex-1 flex-col">
                <div className="absolute right-6 top-4 z-10 flex flex-col gap-3 items-end">
                    <AuthControls />
                    {error && (
                        <div className="rounded-lg bg-red-900/40 border border-red-500/40 px-3 py-2 text-sm text-red-100 max-w-xs">
                            {error}
                        </div>
                    )}
                    <button
                        type="button"
                        onClick={handleReset}
                        className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 transition-colors"
                        aria-label="Reset conversation"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.7"
                            className="h-4 w-4"
                        >
                            <path d="M3 12a9 9 0 1 0 3-6.708" />
                            <path d="M3 3v5h5" />
                        </svg>
                        Reset conversation
                    </button>
                </div>
                <div className="flex flex-1 flex-col overflow-y-auto p-6 md:p-10">
                    <div className="flex max-w-4xl mx-auto w-full flex-1 flex-col justify-end">
                        <div className="space-y-8">
                            {messages.map((message, index) => (
                                <Message key={index} {...message} />
                            ))}
                            <div ref={bottomRef} />
                        </div>
                    </div>
                </div>
                <ChatInput onSend={handleSend} />
            </main>
        </div>
    );
}
