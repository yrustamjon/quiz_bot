import { useState } from "react";
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
}: {
  quiz: any;
  onSaved: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [values, setValues] = useState<any>(quiz);
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        try {
          const data = { ...values };
          delete data.id;
          delete data.owner;
          delete data.available_questions;
          await api(`quizzes/${quiz.id}/`, {
            method: "PATCH",
            body: JSON.stringify(data),
          });
          setNotice("Sozlamalar saqlandi.");
          onSaved();
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <fieldset disabled={quiz.status !== "draft" || busy}>
        <div className="two-col">
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
                value={values[key]}
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
        <label>
          Tavsif
          <textarea
            value={values.description}
            onChange={(e) =>
              setValues({ ...values, description: e.target.value })
            }
          />
        </label>
        <div className="two-col">
          <label>
            Navigatsiya
            <select
              value={values.navigation}
              onChange={(e) =>
                setValues({ ...values, navigation: e.target.value })
              }
            >
              <option value="sequential">Ketma-ket — ortga qaytish yo‘q</option>
              <option value="free">Erkin — javobni o‘zgartirish mumkin</option>
            </select>
          </label>
          <label>
            Kirish
            <select
              value={values.access}
              onChange={(e) => setValues({ ...values, access: e.target.value })}
            >
              <option value="public">Ochiq</option>
              <option value="private">Kod bilan</option>
            </select>
          </label>
        </div>
        <div className="two-col">
          {["opens_at", "closes_at"].map((key, i) => (
            <label key={key}>
              {i ? "Yopilish" : "Boshlanish"} vaqti
              <input
                type="datetime-local"
                value={
                  values[key]
                    ? new Date(
                        new Date(values[key]).getTime() -
                          new Date(values[key]).getTimezoneOffset() * 60000,
                      )
                        .toISOString()
                        .slice(0, 16)
                    : ""
                }
                onChange={(e) =>
                  setValues({
                    ...values,
                    [key]: e.target.value
                      ? new Date(e.target.value).toISOString()
                      : null,
                  })
                }
              />
            </label>
          ))}
        </div>
        <label>
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
          {flags.map(([key, label]) => (
            <label
              style={{ display: "flex", alignItems: "center", gap: 10 }}
              key={key}
            >
              <input
                style={{ width: 20, minHeight: 20 }}
                type="checkbox"
                checked={values[key]}
                onChange={(e) =>
                  setValues({ ...values, [key]: e.target.checked })
                }
              />
              {label}
            </label>
          ))}
        </div>
        <div className="notice">
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
      {notice && <p role="status">{notice}</p>}
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
