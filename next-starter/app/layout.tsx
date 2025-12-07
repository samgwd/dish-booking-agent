import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
    title: "Room Booking Agent",
    description: "React + Next.js interface for booking and chat"
};

type RootLayoutProps = {
    children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps): JSX.Element {
    return (
        <html lang="en">
            <body className={`${inter.className} bg-background-light text-slate-900 font-display`}>
                {children}
            </body>
        </html>
    );
}
