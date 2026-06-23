import type { Role } from "./api";

export interface Auth {
  token: string;
  role: Role;
  username: string;
}

const KEY = "medibot_auth";

export function saveAuth(auth: Auth): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, JSON.stringify(auth));
}

export function loadAuth(): Auth | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Auth;
  } catch {
    return null;
  }
}

export function clearAuth(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(KEY);
}
