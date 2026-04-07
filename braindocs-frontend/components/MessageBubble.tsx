"use client";

type MessageSource = {
  source: string;
  score: number;
};

export default function MessageBubble({
  role,
  text,
  sources,
}: {
  role: "user" | "bot";
  text: string;
  sources?: MessageSource[];
}) {
  const isUser = role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} animate-[fadeIn_0.2s_ease]`}
    >
      <div
        className={`
        max-w-[70%] px-4 py-3 border-4 border-black font-bold text-lg
        ${isUser ? "bg-[#FF6B6B] text-white" : "bg-white text-black"}
        shadow-[6px_6px_0px_0px_#000]
        transition-all duration-200
        hover:-translate-y-1 hover:shadow-[10px_10px_0px_0px_#000]
      `}
      >
        {text}

        {/* SOURCES */}
        {sources && sources.length > 0 && (
          <div className="mt-3 text-sm border-t-4 border-black pt-2">
            <p className="font-black uppercase">Sources:</p>
            {sources.map((s, i) => (
              <div key={i}>
                📄 {s.source} ({s.score?.toFixed(2)})
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}