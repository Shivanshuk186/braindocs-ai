"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";

type ChatSession = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
};

const CHAT_SESSIONS_KEY = "chat_sessions_v2";

function createSession(title = "New chat"): ChatSession {
  const now = Date.now();
  return {
    id: `chat_${now}`,
    title,
    createdAt: now,
    updatedAt: now,
  };
}

function sortSessions(items: ChatSession[]): ChatSession[] {
  return [...items].sort((a, b) => b.updatedAt - a.updatedAt);
}

export default function Home() {
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [chatId, setChatId] = useState("");
  const [showSidebar, setShowSidebar] = useState(false);

  useEffect(() => {
    let existing: ChatSession[] = [];
    try {
      const saved = localStorage.getItem(CHAT_SESSIONS_KEY);
      existing = saved ? JSON.parse(saved) : [];
    } catch {
      existing = [];
    }

    const valid = sortSessions(
      existing.filter((x) => typeof x?.id === "string" && typeof x?.title === "string")
    );

    const fresh = createSession();
    localStorage.setItem(`chat_history_${fresh.id}`, "[]");

    setChats(sortSessions([fresh, ...valid]));
    setChatId(fresh.id);
  }, []);

  useEffect(() => {
    localStorage.setItem(CHAT_SESSIONS_KEY, JSON.stringify(chats));
  }, [chats]);

  const createNewChat = useCallback(() => {
    const fresh = createSession();
    localStorage.setItem(`chat_history_${fresh.id}`, "[]");
    setChats((prev) => sortSessions([fresh, ...prev]));
    setChatId(fresh.id);
    setShowSidebar(false);
  }, []);

  const deleteChat = useCallback((id: string) => {
    localStorage.removeItem(`chat_history_${id}`);
    setChats((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (chatId === id) {
        if (next.length > 0) {
          setChatId(next[0].id);
        } else {
          const fresh = createSession();
          localStorage.setItem(`chat_history_${fresh.id}`, "[]");
          setChatId(fresh.id);
          return [fresh];
        }
      }
      return next;
    });
  }, [chatId]);

  const renameChat = useCallback((id: string, title: string) => {
    const clean = title.trim();
    if (!clean) return;
    setChats((prev) =>
      sortSessions(
        prev.map((chat) =>
          chat.id === id
            ? {
                ...chat,
                title: clean,
                updatedAt: Date.now(),
              }
            : chat
        )
      )
    );
  }, []);

  const touchChat = useCallback((id: string) => {
    setChats((prev) =>
      sortSessions(
        prev.map((chat) =>
          chat.id === id
            ? {
                ...chat,
                updatedAt: Date.now(),
              }
            : chat
        )
      )
    );
  }, []);

  const sessionsForSidebar = useMemo(
    () => chats.map(({ id, title, updatedAt }) => ({ id, title, updatedAt })),
    [chats]
  );

  return (
    <div className="h-screen w-full overflow-hidden">
      <div className="md:hidden flex items-center justify-between p-3 border-b-4 border-black bg-white">
        <button
          onClick={() => setShowSidebar((prev) => !prev)}
          className="px-3 py-2 border-2 border-black font-bold"
        >
          History
        </button>
        <button onClick={createNewChat} className="px-3 py-2 border-2 border-black font-bold">
          New chat
        </button>
      </div>

      <div className="flex h-[calc(100vh-64px)] md:h-screen">
        <div className={`${showSidebar ? "flex" : "hidden"} md:flex w-full md:w-auto`}>
          <Sidebar
            chats={sessionsForSidebar}
            currentChat={chatId}
            onCreateChat={createNewChat}
            setCurrentChat={(id) => {
              setChatId(id);
              setShowSidebar(false);
            }}
            onDeleteChat={deleteChat}
          />
        </div>

        <div className="flex-1 min-w-0">
          {chatId && (
            <ChatWindow
              chatId={chatId}
              onChatNamed={(title) => renameChat(chatId, title)}
              onChatActivity={touchChat}
            />
          )}
        </div>
      </div>
    </div>
  );
}