"use client";

import ReactMarkdown from "react-markdown";
import type { Source } from "@/lib/api";
import SourcesAccordion from "./SourcesAccordion";

export interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  retrievalType?: "hybrid_rag" | "sql_rag";
  isRefusal?: boolean;
}

export default function ChatMessage({ role, content, sources, retrievalType, isRefusal }: ChatMessageProps) {
  const isUser = role === "user";
  const refusalStyle = isRefusal
    ? "border-amber-500/60 bg-amber-900/20"
    : "border-slate-700/60 bg-slate-800/60";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-3xl rounded-lg border px-4 py-3 text-sm ${isUser ? "border-blue-600/40 bg-blue-900/30 text-blue-50" : refusalStyle + " text-slate-100"}`}>
        {!isUser && retrievalType && (
          <div className="mb-2 flex items-center gap-2 text-xs">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium ${
                retrievalType === "sql_rag"
                  ? "bg-violet-500/20 text-violet-200 ring-1 ring-inset ring-violet-400/30"
                  : "bg-emerald-500/20 text-emerald-200 ring-1 ring-inset ring-emerald-400/30"
              }`}
            >
              {retrievalType === "sql_rag" ? "SQL RAG" : "Hybrid RAG"}
            </span>
            {isRefusal && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-0.5 text-amber-200 ring-1 ring-inset ring-amber-400/30">
                🔒 RBAC refusal
              </span>
            )}
          </div>
        )}
        {isUser ? (
          <div className="whitespace-pre-wrap">{content}</div>
        ) : (
          <div className="prose prose-invert max-w-none prose-sm prose-p:my-2 prose-ul:my-2 prose-ol:my-2">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
        {!isUser && sources && <SourcesAccordion sources={sources} />}
      </div>
    </div>
  );
}
