"use client";

import { useEffect, useState } from "react";
import { api, type Role } from "@/lib/api";

export default function CollectionsSidebar({ role }: { role: Role }) {
  const [collections, setCollections] = useState<string[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.collectionsForRole(role)
      .then((r) => { if (!cancelled) setCollections(r.collections); })
      .catch((e) => { if (!cancelled) setErr(String(e?.message ?? e)); });
    return () => { cancelled = true; };
  }, [role]);

  return (
    <aside className="w-64 shrink-0 border-r border-slate-800 bg-slate-900/50 p-4">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Your accessible collections
      </h3>
      {err && <div className="text-xs text-red-300">{err}</div>}
      {collections === null ? (
        <div className="text-xs text-slate-500">Loading…</div>
      ) : (
        <ul className="space-y-1">
          {collections.map((c) => (
            <li
              key={c}
              className="rounded-md border border-slate-700/60 bg-slate-800/40 px-3 py-2 text-sm text-slate-200"
            >
              {c}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-6 text-[10px] leading-relaxed text-slate-500">
        RBAC is enforced at the Qdrant retrieval layer. The LLM never sees
        chunks outside these collections.
      </p>
    </aside>
  );
}
