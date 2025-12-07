import "./globals.css";
import { Inter } from "next/font/google";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata = {
    title: "Room Booking Agent",
    description: "React + Next.js interface for booking and chat"
};

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body className={`${inter.className} bg-background-light text-slate-900 font-display`}>{children}</body>
        </html>
    );
}
