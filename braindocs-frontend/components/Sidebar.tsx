"use client";

type Chat = {
  id: string;
  title: string;
  updatedAt: number;
};

export default function Sidebar({
  chats,
  currentChat,
  onCreateChat,
  setCurrentChat,
  onDeleteChat,
}: {
  chats: Chat[];
  currentChat: string;
  onCreateChat: () => void;
  setCurrentChat: (id: string) => void;
  onDeleteChat: (id: string) => void;
}) {
  return (
    <aside className="w-full md:w-72 h-full bg-[#FFD93D] border-r-4 border-black p-4 flex flex-col overflow-hidden">
      <h2 className="font-black text-xl mb-4 border-b-4 border-black pb-2">Chats</h2>

      <button
        onClick={onCreateChat}
        className="mb-4 bg-[#FF6B6B] border-4 border-black font-black py-2 shadow-[4px_4px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none"
      >
        + NEW CHAT
      </button>

      <h3 className="font-black text-sm border-b-2 border-black pb-1 mb-2">History</h3>

      <div className="flex-1 overflow-y-auto space-y-2">
        {chats.length === 0 && <p className="text-sm font-bold">No chats yet</p>}

        {chats.map((chat) => (
          <div
            key={chat.id}
            className={`
              flex items-center justify-between p-2 border-4 border-black cursor-pointer font-bold group
              ${
                currentChat === chat.id
                  ? "bg-[#C4B5FD]"
                  : "bg-white hover:bg-[#FFFDF5]"
              }
            `}
          >
            <button onClick={() => setCurrentChat(chat.id)} className="flex-1 truncate text-left">
              {chat.title}
            </button>
            <button
              onClick={() => onDeleteChat(chat.id)}
              className="ml-2 px-2 py-1 bg-[#FF6B6B] border-2 border-black font-black text-xs opacity-0 group-hover:opacity-100 transition-opacity"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}