"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import ChatInput from "@/components/ChatInput";
import Message, { type MessageProps } from "@/components/Message";

const userAvatar =
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDjK9X3BZOWoc9jiC5v0rOYSnRJdYSxF53hzeB9iyHyFxtdeoKH-9f81MD9GKb5MCwlx14xjpOOdJkv5zYwW8jipICJ2s9GzLA9BZCQFJFymZoDsNTgRrH5fEu4U1l3vxB7E2ehg0pLfA4iymFOLLPvotA331oedtMqsXJ5QnFG8OzxTWl5wabg6T3g7Ke2RmSQgbFViXTQBbCqWQhzZRb4l2pRJhA3jM0wn7puCca_HktpdYFcv0r9RUYpuh9NLBQ1ufxZhrhE9Eo";

const assistantAvatar =
    "https://lh3.googleusercontent.com/aida-public/AB6AXuA1ORR1W1DJE0Mb41HZ2PPHaBJZsPGwKvhCmpWozZrvjBKIx_pfSQtlelyJFaiqAb_0HehE39oTKpqwGlLM2jICKKaCCd1g_qrYKdNCMROEz9rSEl8ofNfoRxf5m7T3DI1-QXhVM7OCeS9uVkBBnOPDftNwfSftgjab9el9n3G_QMojwKzEIsmOoTAoSgWuUTJkvJr5CuQbY6dM5IJvk2fFl04Wy_sNbktQR-8q7-sQFfQ4gpCW6BbWAXsxb22-dSoeXnbB9i3a9Ks";

export default function MessagePage(): JSX.Element {
    const [messages, setMessages] = useState<MessageProps[]>([]);
    const processedInitialMessage = useRef<string | null>(null);
    const bottomRef = useRef<HTMLDivElement | null>(null);

    const addConversationTurn = useCallback((content: string) => {
        const timeStamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        setMessages((prev) => [
            ...prev,
            {
                author: "You",
                time: timeStamp,
                content,
                isUser: true,
                avatarUrl: userAvatar
            },
            {
                author: "AI Assistant",
                time: timeStamp,
                content: `Thanks for your booking request: “${content}”. I’ll find the best option and confirm back.`,
                isUser: false,
                avatarUrl: assistantAvatar
            }
        ]);
    }, []);

    useEffect(() => {
        document.documentElement.classList.add("dark");
        document.body.classList.add("chat-page-body", "font-display");
        return () => {
            document.documentElement.classList.remove("dark");
            document.body.classList.remove("chat-page-body", "font-display");
        };
    }, []);

    useEffect(() => {
        try {
            const incomingMessage = sessionStorage.getItem("initialMessage");
            if (!incomingMessage || processedInitialMessage.current === incomingMessage) return;

            processedInitialMessage.current = incomingMessage;
            sessionStorage.removeItem("initialMessage");
            addConversationTurn(incomingMessage);
        } catch {
            // If storage is unavailable, simply render without a pre-seeded message.
        }
    }, [addConversationTurn]);

    const handleSend = (content: string): void => {
        addConversationTurn(content);
    };

    const handleReset = (): void => {
        setMessages([]);
        processedInitialMessage.current = null;
    };

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    return (
        <div className="relative flex h-screen w-full flex-row overflow-hidden">
            <main className="flex h-full flex-1 flex-col">
                <div className="absolute right-6 top-4 z-10">
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
