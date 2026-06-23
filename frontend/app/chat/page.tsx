"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Role, type Source } from "@/lib/api";
import { loadAuth, clearAuth, type Auth } from "@/lib/auth";
import ChatMessage from "@/components/ChatMessage";
import CollectionsSidebar from "@/components/CollectionsSidebar";
import RoleBadge from "@/components/RoleBadge";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  retrievalType?: "hybrid_rag" | "sql_rag";
  isRefusal?: boolean;
}

export default function ChatPage() {
  const router = useRouter();
  const [auth, setAuth] = useState<Auth | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const a = loadAuth();
    if (!a) { router.replace("/login"); return; }
    setAuth(a);
  }, [router]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  function logout() {
    clearAuth();
    router.replace("/login");
  }

  async function send() {
    if (!auth || !input.trim() || loading) return;
    const q = input.trim();
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chat(auth.token, q);
      const isRefusal = res.sources.length === 0 && res.retrieval_type === "hybrid_rag";
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.answer || "(no answer)",
          sources: res.sources,
          retrievalType: res.retrieval_type,
          isRefusal,
        },
      ]);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `⚠️ ${e?.message ?? "Request failed"}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  if (!auth) return null;

  return (
    <div className="flex h-screen w-full">
      <CollectionsSidebar role={auth.role} />
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900/60 px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="text-lg font-semibold">🏥 MediBot</div>
            <RoleBadge role={auth.role} />
            <span className="text-xs text-slate-500">@{auth.username}</span>
          </div>
          <button
            onClick={logout}
            className="rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:bg-slate-800"
          >
            Sign out
          </button>
        </header>

        <main
          ref={scrollRef}
          className="scrollbar-thin flex-1 overflow-y-auto px-6 py-6"
        >
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.length === 0 && (
              <div className="rounded-md border border-dashed border-slate-700 p-6 text-center text-sm text-slate-400">
                Ask MediBot anything within your authorised collections.
                {auth.role === "nurse" &&
                  " Try “what is the correct IV cannula size for a paediatric patient under 5kg?” to see BM25 + dense hybrid search in action."}
                {auth.role === "billing_executive" &&
                  " Try “how many escalated claims do we have right now?” to see the SQL RAG path."}
              </div>
            )}
            {messages.map((m, i) => (
              <ChatMessage
                key={i}
                role={m.role}
                content={m.content}
                sources={m.sources}
                retrievalType={m.retrievalType}
                isRefusal={m.isRefusal}
              />
            ))}
            {loading && (
              <div className="text-xs text-slate-500">MediBot is thinking…</div>
            )}
          </div>
        </main>

        <footer className="border-t border-slate-800 bg-slate-900/60 px-6 py-3">
          <div className="mx-auto flex max-w-3xl gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              rows={2}
              placeholder="Ask MediBot… (Enter to send, Shift+Enter for newline)"
              className="flex-1 resize-none rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-blue-500 focus:outline-none"
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
