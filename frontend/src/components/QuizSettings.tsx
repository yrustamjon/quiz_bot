import type { Quiz } from "../services/api";
import { tashkentDateInput } from "../services/labels";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
const quizSchema = z.looseObject({
  title: z.string().trim().min(1, "Test nomini kiriting.").max(200),
  subject: z.string().trim().min(1, "Fanni kiriting.").max(100),
  duration_minutes: z.coerce.number().int().min(1).max(1440),
  question_count: z.coerce.number().int().min(1).max(500),
  passing_score: z.coerce.number().min(0).max(100),
  max_attempts: z.coerce.number().int().min(1).max(100),
  navigation: z.enum(["sequential", "free"]),
  access: z.enum(["public", "private"]),
});
import { useUnsavedChanges } from "./useUnsavedChanges";
import { useState, useEffect } from "react";
import { api } from "../services/api";
import { Button } from "./ui/button";
const flags: [string, string][] = [
  ["shuffle_questions", "Savollarni aralashtirish"],
  ["shuffle_options", "Variantlarni aralashtirish"],
  ["show_score", "Ballni ko‘rsatish"],
  ["show_percentage", "Foizni ko‘rsatish"],
  ["show_correct_count", "To‘g‘ri javoblar soni"],
  ["show_incorrect_count", "Noto‘g‘ri javoblar soni"],
  ["show_detailed_answers", "Batafsil javoblarni ochish"],
  ["show_ranking", "Reytingni ko‘rsatish"],
];
export function QuizSettings({
  quiz,
  onSaved,
  section = "basic",
  onDirtyChange,
}: {
  quiz: Quiz;
  onSaved: () => void;
  section?: "basic" | "publishing";
  onDirtyChange?: (dirty: boolean) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [values, setValues] = useState<Quiz>(quiz);
  const [saved, setSaved] = useState<Quiz>(quiz);
  const form = useForm({ resolver: zodResolver(quizSchema), values });
  useUnsavedChanges(
    quiz.status === "draft" && JSON.stringify(values) !== JSON.stringify(saved),
  );
  useEffect(() => {
    onDirtyChange?.(JSON.stringify(values) !== JSON.stringify(saved));
  }, [values, saved, onDirtyChange]);
  return (
    <form
      className="quiz-settings-form"
      onSubmit={form.handleSubmit(async (validated) => {
        setBusy(true);
        setError("");
        try {
          const data = { ...validated };
          delete data.id;
          delete data.owner;
          delete data.available_questions;
          await api(`quizzes/${quiz.id}/`, {
            method: "PATCH",
            body: JSON.stringify(data),
          });
          setNotice("Sozlamalar saqlandi.");
          setSaved({ ...values });
          onSaved();
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      })}
    >
      <fieldset disabled={quiz.status !== "draft" || busy}>
        <div hidden={section !== "basic"} className="two-col">
          {[
            ["title", "Test nomi", "text"],
            ["subject", "Fan", "text"],
            ["duration_minutes", "Davomiylik (daqiqa)", "number"],
            ["question_count", "Savollar soni", "number"],
            ["passing_score", "O‘tish foizi", "number"],
            ["max_attempts", "Urinishlar soni", "number"],
          ].map(([key, label, type]) => (
            <label key={key}>
              {label}
              <input
                type={type}
                required
                value={String(values[key] ?? "")}
                min={key === "passing_score" ? 0 : 1}
                max={
                  key === "passing_score"
                    ? 100
                    : key === "duration_minutes"
                      ? 1440
                      : 500
                }
                onChange={(e) =>
                  setValues({
                    ...values,
                    [key]:
                      type === "number"
                        ? Number(e.target.value)
                        : e.target.value,
                  })
                }
              />
            </label>
          ))}
        </div>
        <label hidden={section !== "basic"}>
          Tavsif
          <textarea
            value={values.description}
            onChange={(e) =>
              setValues({ ...values, description: e.target.value })
            }
          />
        </label>
        <div className="two-col">
          <label hidden={section !== "basic"}>
            Navigatsiya
            <select
              value={values.navigation}
              onChange={(e) =>
                setValues({
                  ...values,
                  navigation: e.target.value as Quiz["navigation"],
                })
              }
            >
              <option value="sequential">Ketma-ket — ortga qaytish yo‘q</option>
              <option value="free">Erkin — javobni o‘zgartirish mumkin</option>
            </select>
          </label>
          <label hidden={section !== "publishing"}>
            Kirish
            <select
              value={values.access}
              onChange={(e) =>
                setValues({
                  ...values,
                  access: e.target.value as Quiz["access"],
                })
              }
            >
              <option value="public">Ochiq</option>
              <option value="private">Kod bilan</option>
            </select>
          </label>
        </div>
        <div hidden={section !== "publishing"} className="two-col">
          {["opens_at", "closes_at"].map((key, i) => (
            <label key={key}>
              {i ? "Yopilish" : "Boshlanish"} vaqti (Toshkent)
              <input
                type="datetime-local"
                value={
                  values[key] ? tashkentDateInput(String(values[key])) : ""
                }
                onChange={(e) =>
                  setValues({
                    ...values,
                    [key]: e.target.value
                      ? new Date(e.target.value + "+05:00").toISOString()
                      : null,
                  })
                }
              />
            </label>
          ))}
        </div>
        <label hidden={section !== "publishing"}>
          Natijalarni e’lon qilish
          <select
            value={values.result_release_mode}
            onChange={(e) =>
              setValues({ ...values, result_release_mode: e.target.value })
            }
          >
            <option value="instant">Urinish tugashi bilan</option>
            <option value="after_close">Test yopilgach</option>
            <option value="manual">O‘qituvchi e’lon qilganda</option>
          </select>
        </label>
        <div className="two-col">
          {flags
            .filter(([key]) =>
              section === "basic"
                ? key.startsWith("shuffle")
                : !key.startsWith("shuffle"),
            )
            .map(([key, label]) => (
              <label
                style={{ display: "flex", alignItems: "center", gap: 10 }}
                key={key}
              >
                <input
                  style={{ width: 20, minHeight: 20 }}
                  type="checkbox"
                  checked={!!values[key]}
                  onChange={(e) =>
                    setValues({ ...values, [key]: e.target.checked })
                  }
                />
                {label}
              </label>
            ))}
        </div>
        <div hidden={section !== "publishing"} className="notice">
          <div>
            <strong>Telegram natijasi namunasi</strong>
            <p>
              {values.result_release_mode !== "instant" ? (
                "Natijangiz saqlandi. Natijalar keyinroq e’lon qilinadi."
              ) : (
                <>
                  {values.title}
                  <br />
                  {values.show_score && "Ball: 8 / 10"}
                  <br />
                  {values.show_percentage && "Natija: 80%"}
                  <br />
                  {values.show_detailed_answers
                    ? "Batafsil javoblar ochiq."
                    : "Javoblar tafsiloti yashirilgan."}
                </>
              )}
            </p>
          </div>
        </div>
        <Button disabled={busy}>
          {busy ? "Saqlanmoqda…" : "Qoralama sozlamalarini saqlash"}
        </Button>
      </fieldset>
      {Object.keys(form.formState.errors).length > 0 && (
        <p role="alert" className="notice error">
          Sozlamalarni tekshiring:{" "}
          {Object.keys(form.formState.errors)
            .map((key) =>
              key === "title"
                ? "Test nomi"
                : key === "subject"
                  ? "Fan"
                  : key === "max_attempts"
                    ? "Urinishlar soni"
                    : "Sonli maydon",
            )
            .join(", ")}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
