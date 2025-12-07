"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function BookingPage() {
  const [inputValue, setInputValue] = useState("");

  useEffect(() => {
    document.body.classList.add("room-booking-agent-body", "text-white", "font-display");
    return () => {
      document.body.classList.remove("room-booking-agent-body", "text-white", "font-display");
    };
  }, []);

  const handleSubmit = (event) => {
    event.preventDefault();
    console.log("Booking query:", inputValue);
    setInputValue("");
  };

  return (
    <main className="relative flex flex-col items-center justify-center p-4 min-h-screen w-full">
      <div
        className="absolute top-0 -left-12 sm:-left-16 w-10 h-10 bg-gray-800/50 rounded-lg shadow-lg flex items-center justify-center"
        style={{ transform: "rotate(-15deg)" }}
      >
        <svg
          className="h-6 w-6 text-gray-400"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      <div
        className="absolute top-2 -right-10 sm:-right-14 w-10 h-10 bg-gray-800/50 rounded-lg shadow-lg flex items-center justify-center"
        style={{ transform: "rotate(15deg)" }}
      >
        <svg
          className="h-6 w-6 text-gray-400"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      <header className="text-center mb-8">
        <h1 className="text-4xl md:text-5xl font-bold text-white tracking-wide">Room Booking Agent</h1>
        <p className="text-gray-400 mt-2 text-lg">Welcome! How can I assist you with your booking today?</p>
      </header>

      <form onSubmit={handleSubmit} className="w-full max-w-2xl">
        <div className="relative">
          <div className="glow-shadow rounded-2xl bg-slate-900/40 p-1.5 backdrop-blur-sm border border-blue-500/20">
            <div className="relative flex items-center">
              <input
                aria-label="Booking query input"
                className="w-full bg-transparent text-gray-200 placeholder-gray-500 border-none focus:ring-0 pl-4 pr-12 py-3 text-base"
                id="booking_query"
                name="booking_query"
                placeholder="e.g., Book a conference room for tomorrow at 10 AM"
                type="text"
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
              />
              <button
                aria-label="Submit booking query"
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-slate-700/60 hover:bg-slate-600/80 p-2 rounded-lg transition-colors duration-200"
                type="submit"
              >
                <svg
                  className="w-5 h-5 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M22 2 11 13" />
                  <path d="m22 2-7 20-4-9-9-4 20-7z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </form>

      <div className="absolute top-4 right-4">
        <Link
          href="/"
          className="bg-slate-700/60 text-white px-4 py-2 rounded-lg hover:bg-slate-600/80 transition-colors"
        >
          Back to Chat
        </Link>
      </div>
    </main>
  );
}
