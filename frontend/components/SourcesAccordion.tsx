"use client";

import { useState } from "react";
import type { Source } from "@/lib/api";

export default function SourcesAccordion({ sources }: { sources: Source[] }) {
  const [open, setOpen] = useState(false);
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-3 border-t border-slate-700/60 pt-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-xs text-slate-400 hover:text-slate-200"
      >
        {open ? "▼" : "▶"} {sources.length} source{sources.length === 1 ? "" : "s"}
      </button>
      {open && (
        <ul className="mt-2 space-y-2 text-xs">
          {sources.map((s, i) => (
            <li key={i} className="rounded-md border border-slate-700/60 bg-slate-900/40 p-2">
              <div className="font-medium text-slate-200">{s.source_document}</div>
              <div className="text-slate-400">Section: {s.section_title}</div>
              <div className="text-slate-500">Collection: {s.collection}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
