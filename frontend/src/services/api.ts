export class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(
      typeof data === "object" ? JSON.stringify(data) : "Ulanishda xatolik",
    );
  }
}
let csrf = "";
export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  if (options.method && options.method !== "GET") {
    const r = await fetch("/api/auth/csrf/", { credentials: "same-origin" });
    csrf = (await r.json()).csrfToken;
  }
  const r = await fetch("/api/" + path, {
    ...options,
    credentials: "same-origin",
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      "X-CSRFToken": csrf,
      ...options.headers,
    },
  });
  if (!r.ok) {
    let data;
    try {
      data = await r.json();
    } catch {
      data = { detail: "Server bilan bog‘lanishda xatolik." };
    }
    throw new ApiError(r.status, data);
  }
  return r.status === 204 ? (undefined as T) : await r.json();
}
export const post = (path: string, data: unknown = {}) =>
  api(path, { method: "POST", body: JSON.stringify(data) });
export type User = {
  id: number;
  username: string;
  full_name: string;
  email: string;
  specialty: string;
  role: string;
  must_change_password: boolean;
};
export type Quiz = {
  [key: string]: any;
  id: number;
  title: string;
  subject: string;
  description: string;
  duration_minutes: number;
  question_count: number;
  available_questions: number;
  status: string;
  access: string;
};
