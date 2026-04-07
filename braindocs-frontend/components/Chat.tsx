"use client";

import { useState } from "react";
import axios from "axios";

type Message = {
  role: "user" | "bot";
  text: string;
};

export default function Chat() {
  const [query, setQuery] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const sendMessage = async () => {
    if (!query) return;

    const userMessage: Message = { role: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const res = await axios.get("http://127.0.0.1:8000/ask", {
        params: { query },
      });

      const botMessage: Message = {
        role: "bot",
        text: res.data.answer,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  };

  const uploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    await axios.post("http://127.0.0.1:8000/upload", formData);
    alert("Uploaded & indexed ✅");
  };

  return (
    <div className="h-screen flex flex-col bg-slate-900 text-white">

      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex justify-between items-center">
        <h1 className="text-xl font-bold">🧠 BrainDocs AI</h1>
        <input type="file" onChange={uploadFile} />
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg max-w-[70%] ${
              msg.role === "user"
                ? "bg-blue-600 ml-auto"
                : "bg-gray-700"
            }`}
          >
            {msg.text}
          </div>
        ))}

        {loading && <div className="text-gray-400">Typing...</div>}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything..."
          className="flex-1 p-3 rounded bg-gray-800 outline-none"
        />
        <button
          onClick={sendMessage}
          className="bg-blue-600 px-4 rounded"
        >
          Send
        </button>
      </div>
    </div>
  );
}