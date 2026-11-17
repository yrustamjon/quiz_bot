import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import QuizDetail from "../pages/QuizDetail";
import { QuizSettings } from "./QuizSettings";
import { ImportDialog } from "./ImportDialog";
import { api, post } from "../services/api";
vi.mock("../services/api", () => ({ api: vi.fn(), post: vi.fn() }));
const quiz = {
  owner_name: "Test",
  participants: 0,
  created_at: "2026-11-17T00:00:00Z",
  updated_at: "2026-11-17T00:00:00Z",
  results_released: false,
  id: 7,
  owner: 9,
  title: "Algebra",
  subject: "Matematika",
  description: "",
  duration_minutes: 30,
  question_count: 1,
  passing_score: 60,
  max_attempts: 1,
  navigation: "sequential" as const,
  access: "public" as const,
  status: "draft",
  available_questions: 1,
  shuffle_questions: false,
  shuffle_options: false,
  show_score: true,
  show_percentage: true,
  show_correct_count: true,
  show_incorrect_count: true,
  show_detailed_answers: false,
  show_ranking: true,
  result_release_mode: "instant",
  opens_at: null,
  closes_at: null,
};
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api).mockImplementation(async (path) => {
    if (path === "quizzes/7/") return quiz;
    if (path === "quizzes/7/questions/") return [{ id: 1, text: "Bir savol" }];
    return { results: [], count: 0 };
  });
  vi.mocked(post).mockResolvedValue(quiz);
});
describe("Quiz and import workflows", () => {
  it("result defaults hide details and preview follows switches", () => {
    render(<QuizSettings quiz={quiz} section="publishing" onSaved={vi.fn()} />);
    const details = screen.getByRole("checkbox", {
      name: "Batafsil javoblarni ochish",
    });
    expect(details).not.toBeChecked();
    expect(
      screen.getByText(/Javoblar tafsiloti yashirilgan/),
    ).toBeInTheDocument();
    fireEvent.click(details);
    expect(details).toBeChecked();
    expect(screen.getByText(/Batafsil javoblar ochiq/)).toBeInTheDocument();
  });
  it("wizard preserves draft edits and prevents publication until saved", async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/quizzes/7"]}>
          <Routes>
            <Route path="quizzes/:id" element={<QuizDetail />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await screen.findByRole("heading", { name: "Algebra" });
    fireEvent.change(screen.getByLabelText("Test nomi"), {
      target: { value: "Yangi algebra" },
    });
    fireEvent.click(screen.getByRole("button", { name: "2. Savollar" }));
    fireEvent.click(screen.getByRole("button", { name: "3. Nashr qilish" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Nashr qilish" }),
      ).toBeDisabled(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "1. Asosiy sozlamalar" }),
    );
    expect(screen.getByLabelText("Test nomi")).toHaveValue("Yangi algebra");
    fireEvent.click(
      screen.getByRole("button", { name: "Qoralama sozlamalarini saqlash" }),
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "quizzes/7/",
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "3. Nashr qilish" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Nashr qilish" }),
      ).toBeEnabled(),
    );
  });
  it("invalid import preview never enables confirmation", async () => {
    vi.mocked(api).mockResolvedValue({
      id: "session",
      rows: [],
      count: 0,
      errors: [{ row: 8, message: "To‘g‘ri javob A–D bo‘lsin." }],
    });
    render(
      <ImportDialog quizId="7" open onClose={vi.fn()} onSaved={vi.fn()} />,
    );
    fireEvent.change(screen.getByLabelText("Import fayli"), {
      target: { files: [new File(["bad"], "questions.xlsx")] },
    });
    await screen.findByText("8-qator: To‘g‘ri javob A–D bo‘lsin.");
    expect(
      screen.getByRole("button", { name: "Importni tasdiqlash" }),
    ).toBeDisabled();
    expect(post).not.toHaveBeenCalled();
  });
});
