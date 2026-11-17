import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { Button } from "../components/ui/button";
import { Loading, ErrorState, Empty } from "../components/states";
export default function Results({
  ranking = false,
  report = false,
}: {
  ranking?: boolean;
  report?: boolean;
}) {
  const [search, setSearch] = useState("");
  const [quiz, setQuiz] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const params = `quiz=${quiz}&search=${encodeURIComponent(search)}&page=${page}`;
  const q = useQuery({
    queryKey: [ranking ? "rankings" : "results", params],
    queryFn: () => api((ranking ? "rankings/" : "results/") + "?" + params),
  });
  const quizzes = useQuery({
    queryKey: ["filter-quizzes"],
    queryFn: () => api("quizzes/"),
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">BILIM TAHLILI</div>
          <h1>{ranking ? "Reyting" : report ? "Hisobotlar" : "Natijalar"}</h1>
          <p>
            {ranking
              ? "Har testdagi eng yaxshi natijalar o‘rtachasi. Tenglikda kamroq vaqt ustun. Bu ko‘rsatkich turli qiyinlikdagi testlarni to‘liq tenglashtirmaydi."
              : "Sizga ruxsat berilgan testlarning haqiqiy natijalari."}
          </p>
        </div>
        {!ranking && (
          <Button
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              setError("");
              try {
                const token = await api("auth/csrf/");
                const r = await fetch("/api/reports/export/?" + params, {
                  method: "POST",
                  credentials: "same-origin",
                  headers: {
                    "X-CSRFToken": token.csrfToken,
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify(quiz ? { quiz: Number(quiz) } : {}),
                });
                if (!r.ok)
                  throw new Error("Eksport bajarilmadi. Filtrni tekshiring.");
                let response = r;
                if (r.status === 202) {
                  const job = await r.json();
                  let ready = false;
                  for (let i = 0; i < 120; i++) {
                    await new Promise((resolve) => setTimeout(resolve, 1000));
                    const state = await api("reports/exports/" + job.id + "/");
                    if (state.status === "failed")
                      throw new Error(state.error || "Eksport bajarilmadi.");
                    if (state.status === "ready") {
                      response = await fetch(
                        "/api/reports/exports/" + job.id + "/download/",
                        { credentials: "same-origin" },
                      );
                      ready = true;
                      break;
                    }
                  }
                  if (!ready)
                    throw new Error(
                      "Hisobot tayyorlanmoqda. Keyinroq qayta tekshiring.",
                    );
                }
                if (!response.ok) throw new Error("Hisobotni yuklab bo‘lmadi.");
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "quiz-results.xlsx";
                a.click();
                URL.revokeObjectURL(url);
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? "Tayyorlanmoqda…" : "Excel eksporti"}
          </Button>
        )}
      </div>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      <section className="card">
        <div className="toolbar">
          <input
            aria-label="O‘quvchi qidirish"
            placeholder="O‘quvchi ismi…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
          <select
            aria-label="Test filtri"
            value={quiz}
            onChange={(e) => {
              setQuiz(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Barcha testlar</option>
            {quizzes.data?.results.map((q: any) => (
              <option key={q.id} value={q.id}>
                {q.title}
              </option>
            ))}
          </select>
        </div>
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorState error={q.error} retry={() => q.refetch()} />
        ) : q.data.results.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {(ranking
                    ? ["O‘rin", "O‘quvchi", "Foiz", "Testlar", "Vaqt (s)"]
                    : [
                        "O‘quvchi",
                        "Test",
                        "To‘g‘ri",
                        "Noto‘g‘ri",
                        "Javobsiz",
                        "Ball",
                        "Foiz",
                        "Holat",
                      ]
                  ).map((x) => (
                    <th key={x}>{x}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {q.data.results.map((x: any) => (
                  <tr key={x.id || x.student_id}>
                    {(ranking
                      ? [
                          x.rank,
                          x.name,
                          Number(x.percentage).toFixed(2) + "%",
                          x.quizzes,
                          x.elapsed_seconds,
                        ]
                      : [
                          x.student_name,
                          x.quiz_title,
                          x.correct,
                          x.incorrect,
                          x.unanswered,
                          `${x.earned}/${x.maximum}`,
                          Number(x.percentage).toFixed(2) + "%",
                          x.status,
                        ]
                    ).map((v: any, i: number) => (
                      <td key={i}>{v}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty text="Hozircha ushbu filtrlar bo‘yicha natijalar mavjud emas." />
        )}
        <div className="pagination">
          <span>{page}-sahifa</span>
          <Button
            variant="outline"
            disabled={!q.data?.previous}
            onClick={() => setPage(page - 1)}
          >
            Oldingi
          </Button>
          <Button
            variant="outline"
            disabled={!q.data?.next}
            onClick={() => setPage(page + 1)}
          >
            Keyingi
          </Button>
        </div>
      </section>
    </>
  );
}
