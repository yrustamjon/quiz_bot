import { useConfirmation } from "../components/ConfirmationProvider";
import { useAuth } from "../services/auth";
import type { Student, Question, Page } from "../services/types";
import { Link } from "react-router-dom";
import { useState } from "react";
import { QuestionEditor } from "../components/QuestionEditor";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post } from "../services/api";
import { Loading, ErrorState, Empty } from "../components/states";
import { Button } from "../components/ui/button";
export default function Directory({
  kind,
}: {
  kind: "students" | "questions";
}) {
  const { user } = useAuth();
  const confirmAction = useConfirmation();
  const [search, setSearch] = useState("");
  const [subject, setSubject] = useState("");
  const [quiz, setQuiz] = useState("");
  const cache = useQueryClient();
  const [editor, setEditor] = useState(false);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<Question>();
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const isQuestion = (row: Question | Student): row is Question =>
    "options" in row;
  const titles = {
    students: "O‘quvchilar",
    questions: "Savollar",
    teachers: "O‘qituvchilar",
  };
  const q = useQuery({
    queryKey: [kind, search, page, subject, quiz],
    queryFn: () =>
      api<Page<Question | Student>>(
        `${kind}/?search=${encodeURIComponent(search)}&page=${page}&subject=${encodeURIComponent(subject)}&quiz=${quiz}`,
      ),
  });
  const quizzes = useQuery({
    queryKey: ["directory-quizzes"],
    queryFn: () => api<Page<import("../services/api").Quiz>>("quizzes/"),
    enabled: kind === "students",
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">MA’LUMOTLAR</div>
          <h1>{titles[kind]}</h1>
          <p>Faqat sizga ruxsat berilgan ma’lumotlar ko‘rsatiladi.</p>
        </div>
        {kind === "questions" && (
          <Button
            onClick={async () => {
              setEditing(undefined);
              setEditor(true);
            }}
          >
            Yangi savol
          </Button>
        )}
      </div>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <section className="card">
        <div className="toolbar">
          {kind === "questions" && (
            <input
              aria-label="Savol fani"
              placeholder="Fan bo‘yicha filtr"
              value={subject}
              onChange={(e) => {
                setSubject(e.target.value);
                setPage(1);
              }}
            />
          )}
          {kind === "students" && (
            <select
              aria-label="Ishtirok etgan test"
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
          )}
          <input
            aria-label="Qidirish"
            placeholder="Qidirish…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorState error={q.error} />
        ) : q.data?.results.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{kind === "questions" ? "Savol" : "Ism"}</th>
                  <th>{kind === "questions" ? "Fan" : "Login"}</th>
                  {kind === "questions" && <th>Amallar</th>}
                  {kind === "students" && (
                    <>
                      <th>Urinishlar</th>
                      <th>O‘rtacha foiz</th>
                      <th>So‘nggi faollik</th>
                      <th>Holat</th>
                      {user?.role === "SUPER_ADMIN" && <th>Amallar</th>}
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {q.data.results.map((x) => (
                  <tr key={x.id}>
                    <td>
                      {!isQuestion(x) ? (
                        <Link className="text-link" to={"/students/" + x.id}>
                          {x.full_name}
                        </Link>
                      ) : (
                        x.text
                      )}
                    </td>
                    <td>
                      {isQuestion(x) ? x.subject : x.telegram_username || "—"}
                    </td>
                    {!isQuestion(x) && (
                      <>
                        <td>{x.participation_count}</td>
                        <td>{x.average_percentage ?? "—"}%</td>
                        <td>
                          {x.last_activity
                            ? new Date(x.last_activity).toLocaleDateString(
                                "uz-UZ",
                                { timeZone: "Asia/Tashkent" },
                              )
                            : "—"}
                        </td>
                        <td>{x.is_active ? "Faol" : "Nofaol"}</td>
                        {user?.role === "SUPER_ADMIN" && (
                          <td>
                            <Button
                              variant="outline"
                              disabled={busy}
                              onClick={async () => {
                                if (
                                  !(await confirmAction(
                                    x.is_active
                                      ? "O‘quvchi hisobini cheklaysizmi?"
                                      : "Hisobni faollashtirasizmi?",
                                  ))
                                )
                                  return;
                                setBusy(true);
                                try {
                                  await post(
                                    `students/${x.id}/${x.is_active ? "deactivate" : "activate"}/`,
                                  );
                                  cache.invalidateQueries({
                                    queryKey: ["students"],
                                  });
                                } catch (e) {
                                  setError((e as Error).message);
                                } finally {
                                  setBusy(false);
                                }
                              }}
                            >
                              {x.is_active ? "Nofaol qilish" : "Faollashtirish"}
                            </Button>
                          </td>
                        )}
                      </>
                    )}
                    {isQuestion(x) && (
                      <td>
                        <div className="actions">
                          <Button
                            variant="outline"
                            disabled={busy}
                            onClick={async () => {
                              setBusy(true);
                              try {
                                await post(`questions/${x.id}/duplicate/`);
                                cache.invalidateQueries({
                                  queryKey: ["questions"],
                                });
                              } catch (e) {
                                setError((e as Error).message);
                              } finally {
                                setBusy(false);
                              }
                            }}
                          >
                            Nusxalash
                          </Button>
                          <Button
                            variant="outline"
                            onClick={async () => {
                              setEditing(x);
                              setEditor(true);
                            }}
                          >
                            Tahrirlash
                          </Button>
                          <Button
                            variant="outline"
                            onClick={async () => {
                              if (
                                !(await confirmAction("Savol o‘chirilsinmi?"))
                              )
                                return;
                              try {
                                await api("questions/" + x.id + "/", {
                                  method: "DELETE",
                                });
                                cache.invalidateQueries({
                                  queryKey: ["questions"],
                                });
                              } catch (e) {
                                setError((e as Error).message);
                              }
                            }}
                          >
                            O‘chirish
                          </Button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            text={search ? "Qidiruvga mos ma’lumot topilmadi." : undefined}
          />
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
      {editor && (
        <QuestionEditor
          key={editing?.id || "new"}
          question={editing}
          open={editor}
          onClose={() => setEditor(false)}
          onSaved={() => {
            cache.invalidateQueries({ queryKey: ["questions"] });
          }}
        />
      )}
    </>
  );
}
