"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Role } from "@/lib/api";
import { saveAuth } from "@/lib/auth";

const DEMO_USERS: Array<{ username: string; password: string; role: Role; label: string }> = [
  { username: "dr.mehta",     password: "Doctor#1",  role: "doctor",            label: "Doctor (Dr. Mehta)" },
  { username: "nurse.priya",  password: "Nurse#1",   role: "nurse",             label: "Nurse (Priya)" },
  { username: "billing.ravi", password: "Billing#1", role: "billing_executive", label: "Billing (Ravi)" },
  { username: "tech.anand",   password: "Tech#1",    role: "technician",        label: "Technician (Anand)" },
  { username: "admin.sys",    password: "Admin#1",   role: "admin",             label: "Admin" },
];

export default function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function doLogin(u: string, p: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(u, p);
      saveAuth({ token: res.token, role: res.role, username: res.username });
      router.push("/chat");
    } catch (e: any) {
      setError(e?.message ?? "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <form
        onSubmit={(e) => { e.preventDefault(); doLogin(username, password); }}
        className="space-y-4"
      >
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-300">Username</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 focus:border-blue-500 focus:outline-none"
            placeholder="e.g. dr.mehta"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-300">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 focus:border-blue-500 focus:outline-none"
            placeholder="••••••••"
            required
          />
        </div>
        {error && (
          <div className="rounded-md border border-red-600/40 bg-red-900/30 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <div className="space-y-3">
        <div className="text-sm text-slate-400">Try a demo account:</div>
        <div className="grid gap-2">
          {DEMO_USERS.map((u) => (
            <button
              key={u.username}
              type="button"
              disabled={loading}
              onClick={() => doLogin(u.username, u.password)}
              className="w-full rounded-md border border-slate-700 bg-slate-800/60 px-4 py-3 text-left hover:border-slate-500 hover:bg-slate-800"
            >
              <div className="font-medium text-slate-100">{u.label}</div>
              <div className="text-xs text-slate-400">
                {u.username} &middot; {u.password}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
