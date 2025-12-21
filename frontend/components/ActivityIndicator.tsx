"use client";

export type ActivityIndicatorProps = {
    activities: string[];
};

/**
 * A pulsing activity indicator that displays what the AI agent is currently doing.
 * Shows tool calls in a visually appealing animated format.
 */
export default function ActivityIndicator({ activities }: ActivityIndicatorProps): JSX.Element | null {
    if (activities.length === 0) return null;

    const latestActivity = activities[activities.length - 1];

    return (
        <div className="flex gap-4 animate-fadeIn">
            {/* Pulsing avatar placeholder */}
            <div className="relative size-10 flex-shrink-0">
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 opacity-50 animate-pulse" />
                <div className="absolute inset-1 rounded-full bg-slate-900 flex items-center justify-center">
                    <svg
                        className="w-5 h-5 text-indigo-400 animate-spin-slow"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                    >
                        <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                        <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
                    </svg>
                </div>
            </div>

            {/* Activity content */}
            <div className="flex flex-1 flex-col items-start gap-1">
                <p className="text-slate-400 text-sm font-medium">
                    AI Assistant
                </p>
                <div className="bg-slate-800/50 border border-slate-700/30 px-4 py-3 rounded-xl rounded-tl-none">
                    <div className="flex items-center gap-3">
                        {/* Animated dots */}
                        <div className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce-dot" style={{ animationDelay: "0ms" }} />
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce-dot" style={{ animationDelay: "150ms" }} />
                            <span className="w-1.5 h-1.5 rounded-full bg-pink-400 animate-bounce-dot" style={{ animationDelay: "300ms" }} />
                        </div>
                        {/* Activity text */}
                        <p className="text-slate-200 text-base leading-relaxed">
                            {latestActivity}
                        </p>
                    </div>

                    {/* Show previous activities if there are multiple */}
                    {activities.length > 1 && (
                        <div className="mt-3 pt-3 border-t border-slate-700/30">
                            <ul className="space-y-1.5">
                                {activities.slice(0, -1).map((activity, index) => (
                                    <li
                                        key={index}
                                        className="text-slate-400 text-sm flex items-center gap-2"
                                    >
                                        <svg className="w-4 h-4 text-emerald-500 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                        <span>{activity}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
