const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Role =
  | "doctor"
  | "nurse"
  | "billing_executive"
  | "technician"
  | "admin";

export interface Source {
  source_document: string;
  section_title: string;
  collection: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  retrieval_type: "hybrid_rag" | "sql_rag";
  role: Role;
}

export interface LoginResponse {
  token: string;
  role: Role;
  username: string;
}

async function request<T>(
  path: string,
  init: RequestInit & { token?: string } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (init.token) headers.Authorization = `Bearer ${init.token}`;

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore
    }
    if (res.status === 401) {
      // Token bad/expired — clear auth and bounce to login.
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("medibot_auth");
        window.location.href = "/login";
      }
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  login: (username: string, password: string) =>
    request<LoginResponse>("/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  chat: (token: string, question: string) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      token,
      body: JSON.stringify({ question }),
    }),
  collectionsForRole: (role: Role) =>
    request<{ role: Role; collections: string[] }>(`/collections/${role}`),
};
