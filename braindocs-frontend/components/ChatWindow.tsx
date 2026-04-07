"use client";

import { useState, useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

type Source = {
  source: string;
  score: number;
  page?: number;
};

type Message = {
  role: "user" | "bot";
  text: string;
  sources?: Source[];
};

type IndexedDoc = {
  source: string;
  chunks: number;
  pages: number;
};

export default function ChatWindow({
  chatId,
  onChatNamed,
  onChatActivity,
}: {
  chatId: string;
  onChatNamed: (title: string) => void;
  onChatActivity: (id: string) => void;
}) {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const [docs, setDocs] = useState<IndexedDoc[]>([]);

  const bottomRef = useRef<HTMLDivElement>(null);

  const titleFromPrompt = (text: string) => {
    const clean = text.replace(/\s+/g, " ").trim();
    if (!clean) return "New chat";
    return clean.length > 40 ? `${clean.slice(0, 40)}...` : clean;
  };

  useEffect(() => {
    try {
      const saved = localStorage.getItem(`chat_history_${chatId}`);
      if (saved) {
        setMessages(JSON.parse(saved));
      } else {
        setMessages([]);
      }
    } catch {
      setMessages([]);
    }
  }, [chatId]);

  useEffect(() => {
    localStorage.setItem(`chat_history_${chatId}`, JSON.stringify(messages));
  }, [messages, chatId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch(`${backendUrl}/health`, { cache: "no-store" });
        setStatus(res.ok ? "online" : "offline");
      } catch {
        setStatus("offline");
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 5000);
    return () => clearInterval(interval);
  }, [backendUrl]);

  useEffect(() => {
    const fetchDocs = async () => {
      if (status !== "online") return;
      try {
        const res = await fetch(`${backendUrl}/documents`, { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
        setDocs(Array.isArray(data?.documents) ? data.documents : []);
      } catch {
        // Ignore docs panel fetch errors to keep chat unaffected.
      }
    };

    fetchDocs();
    const interval = setInterval(fetchDocs, 8000);
    return () => clearInterval(interval);
  }, [backendUrl, status, uploadState]);

  const sendMessage = async () => {
    const currentQuery = query.trim();
    if (!currentQuery || status !== "online" || loading) return;

    if (messages.filter((m) => m.role === "user").length === 0) {
      onChatNamed(titleFromPrompt(currentQuery));
    }
    onChatActivity(chatId);

    const userMsg: Message = { role: "user", text: currentQuery };
    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);

    try {
      const res = await fetch(`${backendUrl}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: currentQuery }),
      });

      if (!res.ok) {
        throw new Error(`Ask failed (${res.status})`);
      }

      const data = await res.json();

      const botMsg: Message = {
        role: "bot",
        text: typeof data.answer === "string" ? data.answer : "I don't know",
        sources: Array.isArray(data.sources) ? data.sources : [],
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: "Backend request failed. Please check server logs and try again.",
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (status !== "online") {
      setUploadState("error");
      setUploadMessage("Backend is offline. Start backend and retry upload.");
      e.target.value = "";
      return;
    }

    const allowed = [
      ".pdf",
      ".csv",
      ".txt",
      ".doc",
      ".docx",
      ".xls",
      ".xlsx",
      ".png",
      ".jpg",
      ".jpeg",
      ".webp",
      ".bmp",
      ".tif",
      ".tiff",
    ];
    const lowerName = file.name.toLowerCase();
    if (!allowed.some((ext) => lowerName.endsWith(ext))) {
      setUploadState("error");
      setUploadMessage(
        "Supported formats: PDF, CSV, TXT, DOC, DOCX, XLS, XLSX, PNG, JPG, JPEG, WEBP, BMP, TIF, TIFF."
      );
      e.target.value = "";
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploadState("uploading");
    setUploadMessage(`Uploading ${file.name}...`);

    try {
      const res = await fetch(`${backendUrl}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data?.detail || `Upload failed (${res.status})`);
      }

      setUploadState("success");
      setUploadMessage(data?.message || `${file.name} uploaded and indexed.`);
      onChatActivity(chatId);
      if (Array.isArray(data?.documents)) {
        setDocs(data.documents);
      }
    } catch (error) {
      console.error(error);
      setUploadState("error");
      setUploadMessage(error instanceof Error ? error.message : "Upload failed");
    } finally {
      e.target.value = "";
    }
  };

  return (
    <div className="h-full min-h-0 bg-[#FFFDF5] text-black flex">
      <div className="flex flex-col flex-1 min-w-0 h-full border-r-4 border-black">
        <div className="p-3 border-b-4 border-black bg-[#C4B5FD] font-bold flex justify-between items-center">
          <div>
            {status === "checking" && "Checking backend..."}
            {status === "online" && "Backend Connected"}
            {status === "offline" && "Backend Offline"}
          </div>

          <label
            className={`px-4 py-2 border-4 border-black cursor-pointer ${
              status === "online" ? "bg-black text-white" : "bg-gray-300 text-gray-600"
            }`}
          >
            Upload File
            <input type="file" hidden onChange={handleUpload} disabled={status !== "online" || uploadState === "uploading"} />
          </label>
        </div>

        {uploadState !== "idle" && (
          <div
            className={`mx-4 mt-3 px-4 py-2 border-2 text-sm font-semibold ${
              uploadState === "success"
                ? "bg-green-100 border-green-700 text-green-800"
                : uploadState === "error"
                ? "bg-red-100 border-red-700 text-red-800"
                : "bg-yellow-100 border-yellow-700 text-yellow-800"
            }`}
          >
            {uploadMessage}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && <p className="font-bold">Start a new conversation. Your old chats are in History.</p>}

          {messages.map((msg, i) => (
            <MessageBubble key={i} role={msg.role} text={msg.text} sources={msg.sources} />
          ))}

          {loading && <div className="font-bold animate-pulse">Thinking...</div>}

          <div ref={bottomRef} />
        </div>

        <div className="p-4 border-t-4 border-black bg-white flex gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask anything"
            className="flex-1 h-14 px-4 border-4 border-black font-bold text-lg outline-none"
          />

          <button
            onClick={sendMessage}
            disabled={status !== "online" || loading}
            className="h-14 px-6 bg-[#FF6B6B] border-4 border-black font-black disabled:opacity-50"
          >
            {loading ? "WAIT..." : "SEND"}
          </button>
        </div>
      </div>

      <aside className="hidden xl:flex w-80 h-full flex-col bg-white">
        <div className="p-3 border-b-4 border-black font-black">Indexed Documents</div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {docs.length === 0 && <p className="text-sm font-bold">No indexed documents yet.</p>}

          {docs.map((doc) => (
            <div key={doc.source} className="border-2 border-black p-2 font-bold">
              <div className="truncate">{doc.source}</div>
              <div className="text-xs mt-1">Chunks: {doc.chunks}</div>
              <div className="text-xs">Pages/Rows: {doc.pages}</div>
            </div>
          ))}
        </div>
      </aside>

      <div className="xl:hidden fixed right-3 top-20 w-56 max-h-[45vh] bg-white border-4 border-black overflow-y-auto p-2 space-y-2">
        <div className="font-black text-sm border-b-2 border-black pb-1">Indexed Docs</div>
        {docs.length === 0 && <p className="text-xs font-bold">No indexed documents yet.</p>}
        {docs.map((doc) => (
          <div key={doc.source} className="border-2 border-black p-2 text-xs font-bold">
            <div className="truncate">{doc.source}</div>
            <div>Chunks: {doc.chunks}</div>
          </div>
        ))}
      </div>
    </div>
  );
}