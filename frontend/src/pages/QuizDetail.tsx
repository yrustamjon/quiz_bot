import { useConfirmation } from "../components/ConfirmationProvider";
import { QuizActions } from "../components/QuizActions";
import type { Question, CommandResponse } from "../services/types";
import { statusLabel } from "../services/labels";
import { QuestionBank } from "../components/QuestionBank";
import { QuizSettings } from "../components/QuizSettings";
import { QuestionEditor } from "../components/QuestionEditor";
import { ImportDialog } from "../components/ImportDialog";
import { useState } from "react";
import { useParams, Link, useSearchParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post, type Quiz } from "../services/api";
import { Button } from "../components/ui/button";
import { Loading, ErrorState, Empty } from "../components/states";
export default function QuizDetail() {
  const confirmAction = useConfirmation();
  const { id } = useParams();
  const [urlParams] = useSearchParams();
  const [step, setStep] = useState(urlParams.has("import") ? 2 : 1);
  const [configDirty, setConfigDirty] = useState(false);
  function move(next: number) {
    const form = document.querySelector<HTMLFormElement>(".quiz-settings-form");
    if (step === 1 && form && !form.reportValidity()) return;
    setStep(next);
  }
  const [editor, setEditor] = useState(false);
  const [importOpen, setImportOpen] = useState(urlParams.has("import"));
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const c = useQueryClient();
  const q = useQuery({
    queryKey: ["quiz", id],
    queryFn: () => api<Quiz>("quizzes/" + id + "/"),
  });
  const questions = useQuery({
    queryKey: ["quiz-questions", id],
    queryFn: () => api<Question[]>("quizzes/" + id + "/questions/"),
  });
  if (q.isPending) return <Loading />;
  if (q.error) return <ErrorState error={q.error} />;
  const quiz = q.data!;
  async function action(path: string) {
    setBusy(true);
    setError("");
    try {
      const d = await post<Quiz & CommandResponse>(`quizzes/${id}/${path}/`);
      setMessage(
        d.code || d.access_code
          ? "Kirish kodi: " + (d.code || d.access_code)
          : "Amal bajarildi.",
      );
      c.invalidateQueries({ queryKey: ["quiz", id] });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">TEST TAFSILOTLARI</div>
          <h1>{quiz.title}</h1>
          <p>
            {quiz.subject} · {quiz.duration_minutes} daqiqa ·{" "}
            {quiz.question_count} savol
          </p>
        </div>
        <QuizActions quiz={quiz} />
      </div>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="notice">
          {message}
        </p>
      )}
      <div
        className="actions"
        style={{ marginBottom: 24 }}
        role="group"
        aria-label="Test yaratish bosqichlari"
      >
        {["Asosiy sozlamalar", "Savollar", "Nashr qilish"].map((label, i) => (
          <Button
            key={label}
            aria-pressed={step === i + 1}
            variant={step === i + 1 ? "default" : "outline"}
            onClick={() => move(i + 1)}
          >
            {i + 1}. {label}
          </Button>
        ))}
      </div>
      {
        <>
          <section hidden={step !== 1 && step !== 3} className="card padded">
            <QuizSettings
              key={quiz.id + quiz.status}
              quiz={quiz}
              section={step === 3 ? "publishing" : "basic"}
              onDirtyChange={setConfigDirty}
              onSaved={() => c.invalidateQueries({ queryKey: ["quiz", id] })}
            />
          </section>
          <div hidden={step === 1} style={{ display: "grid", gap: 20 }}>
            <section hidden={step !== 3} className="card padded">
              <h2>Nashrga tayyorgarlik</h2>
              <p>
                Savollar: {quiz.available_questions}/{quiz.question_count}
              </p>
              <p>Holat: {statusLabel[quiz.status] || quiz.status}</p>
              <p>
                Faol test tarkibi saqlanadi. O‘zgartirish uchun nusxa yarating.
              </p>
              {configDirty && (
                <p role="status">Nashr qilishdan oldin sozlamalarni saqlang.</p>
              )}
              <div className="actions">
                {quiz.result_release_mode === "manual" &&
                  quiz.status !== "draft" &&
                  !quiz.results_released && (
                    <Button
                      disabled={busy}
                      onClick={async () => {
                        if (
                          await confirmAction(
                            "Natijalarni qatnashuvchilarga e’lon qilasizmi?",
                          )
                        )
                          action("release-results");
                      }}
                    >
                      Natijalarni e’lon qilish
                    </Button>
                  )}
                {["closed", "draft"].includes(quiz.status) && (
                  <Button
                    variant="outline"
                    disabled={busy}
                    onClick={async () => {
                      if (await confirmAction("Test arxivlansinmi?"))
                        action("archive");
                    }}
                  >
                    Arxivlash
                  </Button>
                )}
                {quiz.status === "draft" && (
                  <Button
                    disabled={busy || configDirty}
                    onClick={() => action("publish")}
                  >
                    Nashr qilish
                  </Button>
                )}
                {quiz.status === "published" && (
                  <Button
                    disabled={busy}
                    onClick={async () => {
                      if (await confirmAction("Testni yopasizmi?"))
                        action("close");
                    }}
                  >
                    Testni yopish
                  </Button>
                )}
                <Button
                  disabled={busy}
                  variant="outline"
                  onClick={() => action("duplicate")}
                >
                  Nusxa yaratish
                </Button>
              </div>
            </section>
            <section hidden={step !== 2} className="card padded">
              <h2>Savollar</h2>
              {quiz.status === "draft" && (
                <QuestionBank
                  quizId={id!}
                  ownerId={quiz.owner}
                  selected={questions.data || []}
                  onSaved={() => {
                    c.invalidateQueries({ queryKey: ["quiz-questions", id] });
                    c.invalidateQueries({ queryKey: ["quiz", id] });
                  }}
                />
              )}
              {quiz.status === "draft" && (
                <div className="actions">
                  <Button onClick={() => setEditor(true)}>
                    Savol qo‘shish
                  </Button>
                  <Button variant="outline" onClick={() => setImportOpen(true)}>
                    Excel importi
                  </Button>
                </div>
              )}
              {questions.isPending ? (
                <Loading />
              ) : questions.error ? (
                <ErrorState error={questions.error} />
              ) : questions.data?.length ? (
                questions.data.map((x, i) => (
                  <p key={x.id}>
                    {i + 1}. {x.text}
                  </p>
                ))
              ) : (
                <Empty text="Testga savol qo‘shilmagan." />
              )}
            </section>
          </div>
        </>
      }
      <div className="actions">
        <Button
          variant="outline"
          disabled={step === 1}
          onClick={() => move(step - 1)}
        >
          Oldingi
        </Button>
        <Button disabled={step === 3} onClick={() => move(step + 1)}>
          Keyingi
        </Button>
        <Link className="button secondary-button" to="/quizzes">
          Testlarga qaytish
        </Link>
      </div>
      <QuestionEditor
        open={editor}
        onClose={() => setEditor(false)}
        onSaved={async (questionId) => {
          const ids = (questions.data || []).map((q) => q.id);
          await api(`quizzes/${id}/questions/`, {
            method: "PUT",
            body: JSON.stringify({ question_ids: [...ids, questionId] }),
          });
          c.invalidateQueries({ queryKey: ["quiz-questions", id] });
          c.invalidateQueries({ queryKey: ["quiz", id] });
        }}
      />
      <ImportDialog
        quizId={id!}
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onSaved={() => {
          c.invalidateQueries({ queryKey: ["quiz-questions", id] });
          c.invalidateQueries({ queryKey: ["quiz", id] });
        }}
      />
    </>
  );
}
