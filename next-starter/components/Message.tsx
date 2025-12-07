"use client";

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
              <p className="text-white text-base font-normal leading-relaxed">{content}</p>
            </div>
          </div>
        </div>
      )}

      <div
        className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 flex-shrink-0"
        style={{ backgroundImage: `url("${avatarUrl}")` }}
        aria-label={`${author} avatar`}
      />

      {!isUser && (
        <div className={styles.wrapper}>
          <div className="flex flex-col gap-1 w-full max-w-2xl">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <p className={styles.meta}>{author}</p>
              <p className="text-slate-400 text-sm font-normal leading-normal">{time}</p>
            </div>
            <div className={styles.bubble}>
              <p className="text-white text-base font-normal leading-relaxed">{content}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
