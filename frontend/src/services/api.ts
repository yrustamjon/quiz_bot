function errorMessage(data: unknown): string {
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.map(errorMessage).join(" ");
  if (data && typeof data === "object") {
    const labels: Record<string, string> = {
      username: "Login",
      email: "Email",
      full_name: "Ism",
      password: "Parol",
      new_password: "Yangi parol",
      old_password: "Amaldagi parol",
      subject: "Fan",
      title: "Test nomi",
      points: "Ball",
      options: "Variantlar",
      correct_option: "To‘g‘ri javob",
    };
    return Object.entries(data)
      .map(
        ([key, value]) =>
          (key === "detail" ? "" : (labels[key] || "Maydon") + ": ") +
          errorMessage(value),
      )
      .join(" ");
  }
  return "So‘rovni bajarib bo‘lmadi.";
}
export class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(errorMessage(data));
  }
}
async function request(url: string, options: RequestInit): Promise<Response> {
  try {
    return await fetch(url, options);
  } catch {
    throw new ApiError(0, {
      detail: "Internet bilan bog‘lanishda muammo yuz berdi.",
    });
  }
}
let csrf = "";
export async function api<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  if (options.method && options.method !== "GET") {
    const r = await request("/api/auth/csrf/", { credentials: "same-origin" });
    if (!r.ok)
      throw new ApiError(r.status, { detail: "Sessiyani tekshirib bo‘lmadi." });
    csrf = (await r.json()).csrfToken;
  }
  const r = await request("/api/" + path, {
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
    if ([401, 403].includes(r.status) && !path.startsWith("auth/"))
      window.dispatchEvent(new Event("auth-check-required"));
    throw new ApiError(r.status, data);
  }
  let data: unknown;
  try {
    data = r.status === 204 ? undefined : await r.json();
  } catch {
    throw new ApiError(502, { detail: "Server javobini o‘qib bo‘lmadi." });
  }
  if (
    options.method &&
    options.method !== "GET" &&
    !path.includes("import/preview")
  )
    window.dispatchEvent(
      new CustomEvent("mutation-success", {
        detail:
          path === "auth/login/"
            ? "Hisobga kirildi."
            : path === "auth/logout/"
              ? "Hisobdan chiqildi."
              : path.includes("import/confirm")
                ? "Savollar import qilindi."
                : "O‘zgarishlar saqlandi.",
      }),
    );
  return data as T;
}
export const post = <T = unknown>(path: string, data: unknown = {}) =>
  api<T>(path, { method: "POST", body: JSON.stringify(data) });
export type User = {
  id: number;
  username: string;
  full_name: string;
  email: string;
  specialty: string;
  role: string;
  must_change_password: boolean;
  is_active: boolean;
  quiz_count?:number;
  created_at: string;
};
export type Quiz = {
  [key: string]: string | number | boolean | null | undefined;
  access_code?:string|null;
  owner: number;
  owner_name: string;
  participants: number;
  created_at: string;
  updated_at: string;
  passing_score: string | number;
  max_attempts: number;
  navigation: "sequential" | "free";
  shuffle_questions: boolean;
  shuffle_options: boolean;
  opens_at: string | null;
  closes_at: string | null;
  show_score: boolean;
  show_percentage: boolean;
  show_correct_count: boolean;
  show_incorrect_count: boolean;
  show_detailed_answers: boolean;
  show_ranking: boolean;
  result_release_mode: string;
  results_released: boolean;
  id: number;
  title: string;
  subject: string;
  description: string;
  duration_minutes: number;
  question_count: number;
  available_questions: number;
  status: string;
  access: "public" | "private";
};
