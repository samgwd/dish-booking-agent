"use client";

import Markdown from "react-markdown";

export type MessageProps = {
  author: string;
  time: string;
  content: string;
  isUser: boolean;
  avatarUrl: string;
};

type MessageStyles = {
  container: string;
  wrapper: string;
  meta: string;
  bubble: string;
};

function RobotAvatar(): JSX.Element {
  return (
    <div
      className="size-10 flex-shrink-0 rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-0.5"
      aria-label="AI Assistant avatar"
    >
      <div className="size-full rounded-full bg-slate-900 flex items-center justify-center">
        <svg
          className="w-6 h-6 text-indigo-300"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {/* Robot head */}
          <rect x="4" y="8" width="16" height="12" rx="2" />
          {/* Antenna */}
          <line x1="12" y1="8" x2="12" y2="4" />
          <circle cx="12" cy="3" r="1" fill="currentColor" />
          {/* Eyes */}
          <circle cx="9" cy="13" r="1.5" fill="currentColor" />
          <circle cx="15" cy="13" r="1.5" fill="currentColor" />
          {/* Mouth */}
          <path d="M9 17h6" />
        </svg>
      </div>
    </div>
  );
}

export default function Message({ author, time, content, isUser, avatarUrl }: MessageProps): JSX.Element {
  const user: MessageStyles = {
    container: "flex gap-4 justify-end",
    wrapper: "flex flex-1 flex-col items-end gap-2",
    meta: "text-white text-base font-semibold leading-tight",
    bubble: "bg-primary p-4 rounded-xl rounded-br-none"
  };

  const assistant: MessageStyles = {
    container: "flex gap-4",
    wrapper: "flex flex-1 flex-col items-start gap-2",
    meta: "text-white text-base font-semibold leading-tight",
    bubble: "bg-slate-800 p-4 rounded-xl rounded-tl-none"
  };

  const styles = isUser ? user : assistant;

  const UserAvatar = (
    <div
      className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 flex-shrink-0"
      style={{ backgroundImage: `url("${avatarUrl}")` }}
      aria-label={`${author} avatar`}
    />
  );

  return (
    <div className={styles.container}>
      {isUser && (
        <div className={styles.wrapper}>
          <div className="flex flex-col gap-1 w-full max-w-2xl items-end">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <p className={styles.meta}>{author}</p>
              <p className="text-slate-400 text-sm font-normal leading-normal">{time}</p>
            </div>
            <div className={styles.bubble}>
              <p className="text-white text-base font-normal leading-relaxed whitespace-pre-wrap break-words">
                {content}
              </p>
            </div>
          </div>
        </div>
      )}

      {isUser ? UserAvatar : <RobotAvatar />}

      {!isUser && (
        <div className={styles.wrapper}>
          <div className="flex flex-col gap-1 w-full max-w-2xl">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <p className={styles.meta}>{author}</p>
              <p className="text-slate-400 text-sm font-normal leading-normal">{time}</p>
            </div>
            <div className={styles.bubble}>
              <div className="markdown-content text-white text-base font-normal leading-relaxed break-words">
                <Markdown>{content}</Markdown>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
