"use client";

import { useEffect } from "react";
import Link from "next/link";
import ChatInput from "@/components/ChatInput";
import Message, { type MessageProps } from "@/components/Message";

const messages: MessageProps[] = [
    {
        author: "AI Assistant",
        time: "10:30 AM",
        content:
            "Hello! How can I help you today? You can ask me to draft an email, translate text, or even debug some code.",
        isUser: false,
        avatarUrl:
            "https://lh3.googleusercontent.com/aida-public/AB6AXuA1ORR1W1DJE0Mb41HZ2PPHaBJZsPGwKvhCmpWozZrvjBKIx_pfSQtlelyJFaiqAb_0HehE39oTKpqwGlLM2jICKKaCCd1g_qrYKdNCMROEz9rSEl8ofNfoRxf5m7T3DI1-QXhVM7OCeS9uVkBBnOPDftNwfSftgjab9el9n3G_QMojwKzEIsmOoTAoSgWuUTJkvJr5CuQbY6dM5IJvk2fFl04Wy_sNbktQR-8q7-sQFfQ4gpCW6BbWAXsxb22-dSoeXnbB9i3a9Ks"
    },
    {
        author: "You",
        time: "10:31 AM",
        content: "Draft an email to my team about the new project timeline.",
        isUser: true,
        avatarUrl:
            "https://lh3.googleusercontent.com/aida-public/AB6AXuDjK9X3BZOWoc9jiC5v0rOYSnRJdYSxF53hzeB9iyHyFxtdeoKH-9f81MD9GKb5MCwlx14xjpOOdJkv5zYwW8jipICJ2s9GzLA9BZCQFJFymZoDsNTgRrH5fEu4U1l3vxB7E2ehg0pLfA4iymFOLLPvotA331oedtMqsXJ5QnFG8OzxTWl5wabg6T3g7Ke2RmSQgbFViXTQBbCqWQhzZRb4l2pRJhA3jM0wn7puCca_HktpdYFcv0r9RUYpuh9NLBQ1ufxZhrhE9Eo"
    }
];

export default function HomePage(): JSX.Element {
    useEffect(() => {
        document.documentElement.classList.add("dark");
        document.body.classList.add("chat-page-body", "font-display");
        return () => {
            document.documentElement.classList.remove("dark");
            document.body.classList.remove("chat-page-body", "font-display");
        };
    }, []);

    return (
        <div className="relative flex h-screen w-full flex-row overflow-hidden">
            <main className="flex h-full flex-1 flex-col">
                <div className="flex flex-1 flex-col overflow-y-auto p-6 md:p-10">
                    <div className="flex max-w-4xl mx-auto w-full flex-1 flex-col justify-end">
                        <div className="space-y-8">
                            {messages.map((message, index) => (
                                <Message key={index} {...message} />
                            ))}
                        </div>
                    </div>
                </div>
                <ChatInput />
                <div className="absolute top-4 right-4">
                    <Link
                        href="/booking"
                        className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/80 transition-colors"
                    >
                        Go to Booking Agent
                    </Link>
                </div>
            </main>
        </div>
    );
}
