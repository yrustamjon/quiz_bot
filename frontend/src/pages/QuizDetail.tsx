import { QuestionBank } from "../components/QuestionBank";
import { QuizSettings } from "../components/QuizSettings";
import { QuestionEditor } from "../components/QuestionEditor";
import { ImportDialog } from "../components/ImportDialog";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post, type Quiz } from "../services/api";
import { Button } from "../components/ui/button";
import { Loading, ErrorState, Empty } from "../components/states";
export default function QuizDetail() {
  const { id } = useParams();
  const [step, setStep] = useState(1);
  const [editor, setEditor] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
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
    queryFn: () => api<any[]>("quizzes/" + id + "/questions/"),
  });
  if (q.isPending) return <Loading />;
  if (q.error) return <ErrorState error={q.error} />;
  const quiz = q.data!;
  async function action(path: string) {
    setBusy(true);
    setError("");
    try {
      const d = await post(`quizzes/${id}/${path}/`);
      setMessage(d.code ? "Kirish kodi: " + d.code : "Amal bajarildi.");
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
            onClick={() => setStep(i + 1)}
          >
            {i + 1}. {label}
          </Button>
        ))}
      </div>
      {
        <>
          <section hidden={step !== 1} className="card padded">
            <QuizSettings
              key={quiz.id + quiz.status}
              quiz={quiz}
              onSaved={() => c.invalidateQueries({ queryKey: ["quiz", id] })}
            />
          </section>
          <div hidden={step === 1} className="two-col">
            <section className="card padded">
              <h2>Nashrga tayyorgarlik</h2>
              <p>
                Savollar: {quiz.available_questions}/{quiz.question_count}
              </p>
              <p>Holat: {quiz.status}</p>
              <p>
                Faol test tarkibi saqlanadi. O‘zgartirish uchun nusxa yarating.
              </p>
              <div className="actions">
                {quiz.result_release_mode === "manual" && (
                  <Button
                    disabled={busy}
                    onClick={() => action("release-results")}
                  >
                    Natijalarni e’lon qilish
                  </Button>
                )}
                {["closed", "draft"].includes(quiz.status) && (
                  <Button
                    variant="outline"
                    disabled={busy}
                    onClick={() => {
                      if (confirm("Test arxivlansinmi?")) action("archive");
                    }}
                  >
                    Arxivlash
                  </Button>
                )}
                {quiz.status === "draft" && (
                  <Button disabled={busy} onClick={() => action("publish")}>
                    Nashr qilish
                  </Button>
                )}
                {quiz.status === "published" && (
                  <Button
                    disabled={busy}
                    onClick={() => {
                      if (confirm("Testni yopasizmi?")) action("close");
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
                <Button
                  disabled={busy}
                  variant="outline"
                  onClick={() => action("regenerate-code")}
                >
                  Yangi kirish kodi
                </Button>
              </div>
            </section>
            <section className="card padded">
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
