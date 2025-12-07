"use client";

import { useState } from "react";

const presets = ["Draft an email", "Translate text", "Debug this code"];

export default function ChatInput() {
  const [inputValue, setInputValue] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    // Replace with real handler
    console.log("Sending:", inputValue);
    setInputValue("");
  };

  return (
    <div className="w-full bg-background-light dark:bg-background-dark p-6 md:p-10 pt-4 md:pt-6">
      <div className="mx-auto flex w-full max-w-4xl flex-col items-stretch gap-4">
        <div className="flex gap-3 flex-wrap">
          {presets.map((text) => (
            <button
              key={text}
              type="button"
              className="flex h-8 shrink-0 cursor-pointer items-center justify-center gap-x-2 rounded-lg bg-[#282e39] px-4 text-white hover:bg-primary/80 transition-colors"
            >
              <p className="text-sm font-medium leading-normal">{text}</p>
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex items-center gap-4">
          <label className="flex flex-col min-w-40 h-14 flex-1">
            <div className="flex w-full flex-1 items-stretch rounded-xl h-full bg-[#282e39]">
              <input
                className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl text-white focus:outline-0 focus:ring-2 focus:ring-primary border-none bg-transparent focus:border-none h-full placeholder:text-[#9da6b9] px-4 text-base font-normal leading-normal"
                placeholder="Ask me anything..."
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
              />
              <div className="flex border-none items-center justify-center pr-2">
                <div className="flex items-center gap-1 justify-end">
                  <button
                    type="button"
                    className="flex items-center justify-center p-2 rounded-full text-[#9da6b9] hover:bg-primary/20 hover:text-white transition-colors"
                    aria-label="Attach a file"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      className="w-5 h-5"
                    >
                      <path d="M15.5 8.5 8.75 15.25a2 2 0 1 1-2.83-2.83l7.44-7.44a4 4 0 0 1 5.66 5.66l-7.78 7.78a6 6 0 0 1-8.49-8.49l6.72-6.72" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    className="flex items-center justify-center p-2 rounded-full text-[#9da6b9] hover:bg-primary/20 hover:text-white transition-colors"
                    aria-label="Record audio"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      className="w-5 h-5"
                    >
                      <path d="M12 4a3 3 0 0 0-3 3v5a3 3 0 1 0 6 0V7a3 3 0 0 0-3-3Z" />
                      <path d="M5 10v2a7 7 0 0 0 14 0v-2" />
                      <path d="M12 19v3" />
                      <path d="M8 22h8" />
                    </svg>
                  </button>
                  <button
                    type="submit"
                    className="flex cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-5 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-primary/80 transition-colors"
                  >
                    <span className="truncate">Send</span>
                  </button>
                </div>
              </div>
            </div>
          </label>
        </form>
      </div>
    </div>
  );
}
