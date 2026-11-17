import { formatPercent } from "../services/labels";
import type {
  Result,
  ReportRow,
  Page,
  CsrfToken,
  ExportJob,
} from "../services/types";
import { ExportJobs } from "../components/ExportJobs";
import { statusLabel } from "../services/labels";
import { useAuth } from "../services/auth";
import { useSearchParams } from "react-router-dom";
import { Modal } from "../components/ui/dialog";
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
  const { user } = useAuth();
  const [reportType, setReportType] = useState("results");
  const kind = ranking ? "leaderboard" : report ? reportType : "results";
  const [search, setSearch] = useState("");
  const [teacher, setTeacher] = useState("");
  const [minScore, setMinScore] = useState("");
  const [maxScore, setMaxScore] = useState("");
  const [urlParams] = useSearchParams();
  const [detail, setDetail] = useState<Result>();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [quiz, setQuiz] = useState(urlParams.get("quiz") || "");
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const params = `quiz=${quiz}&search=${encodeURIComponent(search)}&page=${page}&student=${urlParams.get("student") || ""}&start=${start}&end=${end}&teacher=${teacher}&min_score=${minScore}&max_score=${maxScore}`;
  const q = useQuery({
    queryKey: ["report-data", kind, params],
    queryFn: () =>
      api<Page<ReportRow>>(
        (kind === "results"
          ? "results/"
          : kind === "leaderboard"
            ? "rankings/"
            : "reports/summary/?type=" + kind + "&") +
          (kind === "students" || kind === "teachers" ? "" : "?") +
          params,
      ),
  });
  const quizzes = useQuery({
    queryKey: ["filter-quizzes"],
    queryFn: () => api<Page<import("../services/api").Quiz>>("quizzes/"),
  });
  const teachers = useQuery({
    queryKey: ["report-teacher-choices"],
    queryFn: () => api<Page<import("../services/api").User>>("teachers/"),
    enabled: user?.role === "SUPER_ADMIN",
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
        {
          <Button
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              setError("");
              try {
                const token = await api<CsrfToken>("auth/csrf/");
                const r = await fetch("/api/reports/export/?" + params, {
                  method: "POST",
                  credentials: "same-origin",
                  headers: {
                    "X-CSRFToken": token.csrfToken,
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    ...(quiz ? { quiz: Number(quiz) } : {}),
                    report_type: kind,
                  }),
                });
                if (!r.ok)
                  throw new Error("Eksport bajarilmadi. Filtrni tekshiring.");
                let response = r;
                if (r.status === 202) {
                  const job = await r.json();
                  window.dispatchEvent(new Event("export-started"));
                  let ready = false;
                  for (let i = 0; i < 120; i++) {
                    await new Promise((resolve) => setTimeout(resolve, 1000));
                    const state = await api<ExportJob>(
                      "reports/exports/" + job.id + "/",
                    );
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
        }
      </div>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {report && (
        <label>
          Hisobot turi
          <select
            value={reportType}
            onChange={(e) => {
              setReportType(e.target.value);
              setPage(1);
            }}
          >
            <option value="results">Test natijalari</option>
            <option value="students">O‘quvchi ko‘rsatkichlari</option>
            <option value="leaderboard">Reyting hisoboti</option>
            {user?.role === "SUPER_ADMIN" && (
              <option value="teachers">O‘qituvchilar faolligi</option>
            )}
          </select>
        </label>
      )}
      {ranking && (
        <div className="actions" style={{ marginBottom: 20 }}>
          <Button
            variant={!quiz ? "default" : "outline"}
            onClick={() => {
              setQuiz("");
              setPage(1);
            }}
          >
            Umumiy reyting
          </Button>
          <Button
            variant={quiz ? "default" : "outline"}
            disabled={!quizzes.data?.results.length}
            onClick={() => {
              setQuiz(String(quizzes.data?.results[0]?.id || ""));
              setPage(1);
            }}
          >
            Test reytingi
          </Button>
        </div>
      )}
      <section className="card">
        <div className="toolbar report-filters" style={{ flexWrap: "wrap" }}>
          <label>
            Eng kam foiz
            <input
              type="number"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => {
                setMinScore(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label>
            Eng ko‘p foiz
            <input
              type="number"
              min={0}
              max={100}
              value={maxScore}
              onChange={(e) => {
                setMaxScore(e.target.value);
                setPage(1);
              }}
            />
          </label>
          {user?.role === "SUPER_ADMIN" && (
            <label>
              O‘qituvchi filtri
              <select
                value={teacher}
                onChange={(e) => {
                  setTeacher(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Barcha o‘qituvchilar</option>
                {teachers.data?.results.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.full_name || t.username}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label>
            Sanadan
            <input
              type="date"
              value={start}
              onChange={(e) => {
                setStart(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label>
            Sanagacha
            <input
              type="date"
              value={end}
              onChange={(e) => {
                setEnd(e.target.value);
                setPage(1);
              }}
            />
          </label>
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
            {quizzes.data?.results.map((q) => (
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
                  {(kind === "teachers"
                    ? [
                        "O‘qituvchi",
                        "Login",
                        "Testlar",
                        "Urinishlar",
                        "O‘quvchilar",
                        "Foiz",
                      ]
                    : kind === "students"
                      ? ["O‘quvchi", "Urinishlar", "Foiz", "So‘nggi faollik"]
                      : kind === "leaderboard"
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
                {q.data.results.map((x) => (
                  <tr key={x.id || x.student_id || x.quiz__owner_id}>
                    {(kind === "teachers"
                      ? [
                          x.quiz__owner__full_name,
                          x.quiz__owner__username,
                          x.quizzes,
                          x.attempts,
                          x.students,
                          formatPercent(x.percentage) + "%",
                        ]
                      : kind === "students"
                        ? [
                            x.student__full_name,
                            x.attempts,
                            formatPercent(x.percentage) + "%",
                            x.last_activity
                              ? new Date(x.last_activity).toLocaleDateString(
                                  "uz-UZ",
                                  { timeZone: "Asia/Tashkent" },
                                )
                              : "—",
                          ]
                        : kind === "leaderboard"
                          ? [
                              x.rank,
                              x.name,
                              formatPercent(x.percentage) + "%",
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
                              formatPercent(x.percentage) + "%",
                              statusLabel[x.status || ""] || x.status,
                            ]
                    ).map((v, i) => (
                      <td key={i}>
                        {kind === "results" && i === 0 ? (
                          <button
                            className="text-link"
                            onClick={async () => {
                              try {
                                setDetail(
                                  await api<Result>("results/" + x.id + "/"),
                                );
                              } catch (e) {
                                setError((e as Error).message);
                              }
                            }}
                          >
                            {v}
                          </button>
                        ) : (
                          v
                        )}
                      </td>
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
      {report && <ExportJobs />}
      <Modal
        open={!!detail}
        onOpenChange={(v) => {
          if (!v) setDetail(undefined);
        }}
        title="Natija tafsilotlari"
        description="Urinishdagi saqlangan savollar va javoblar asosida hisoblangan."
      >
        {detail && (
          <>
            <h3>{detail.student_name}</h3>
            <p>
              {detail.quiz_title} · {formatPercent(detail.percentage)}%
            </p>
            <p>
              Boshlangan:{" "}
              {new Date(detail.started_at).toLocaleString("uz-UZ", {
                timeZone: "Asia/Tashkent",
              })}{" "}
              · Vaqt: {detail.elapsed_seconds}s
            </p>
            {detail.questions?.map((q) => (
              <section className="notice" key={q.position}>
                <div>
                  <strong>
                    {q.position + 1}. {q.text}
                  </strong>
                  <p>
                    Javob:{" "}
                    {q.selected == null ? "Javobsiz" : q.options[q.selected]}
                  </p>
                  <p>To‘g‘ri javob: {q.options[q.correct_option]}</p>
                </div>
              </section>
            ))}
          </>
        )}
      </Modal>
    </>
  );
}
