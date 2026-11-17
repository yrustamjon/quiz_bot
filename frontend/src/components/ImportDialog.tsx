import { FileUpload } from "./FileUpload";
import type { ImportPreview } from "../services/types";
import { useState } from "react";
import { api, post } from "../services/api";
import { Modal } from "./ui/dialog";
import { Button } from "./ui/button";
export function ImportDialog({
  quizId,
  open,
  onClose,
  onSaved,
}: {
  quizId: string;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [preview, setPreview] = useState<ImportPreview>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  return (
    <Modal
      open={open}
      onOpenChange={(v) => {
        if (!v) onClose();
      }}
      title="Excel orqali savol importi"
      description="1. Fayl yuklash → 2. Tekshirish → 3. Tasdiqlash"
    >
      <a href="/api/questions/import/template/" className="text-link" download>
        Rasmiy XLSX shablonini yuklab olish
      </a>
      <p className="hint">
        XLSX yoki bitta XLSX va rasmlar joylangan ZIP. 10 MB, 500 savolgacha.
        Excel rasmi H ustunidagi savol qatoriga biriktirilsin.
      </p>
      <FileUpload
        label="Import fayli"

        accept=".xlsx,.zip"
        disabled={busy}
        onChange={async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          setError("");
          setConfirmed(false);
          setPreview(undefined);
          if (file.size > 10 * 1024 * 1024) {
            setError("Fayl 10 MB dan oshmasin.");
            return;
          }
          setBusy(true);
          try {
            const data = new FormData();
            data.append("file", file);
            data.append("quiz", quizId);
            setPreview(
              await api<ImportPreview>("questions/import/preview/", {
                method: "POST",
                body: data,
              }),
            );
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      />
      {busy && <p role="status">Tekshirilmoqda…</p>}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {preview && (
        <>
          <h3>{preview.count} ta savol</h3>
          <p className="hint">
            Jami: {preview.total_rows ?? preview.count} · To‘g‘ri:{" "}
            {preview.count} · Xatoli:{" "}
            {preview.invalid_rows ?? preview.errors.length} · Rasmlar:{" "}
            {preview.image_count ?? 0}
          </p>
          {preview.errors.map((e, i) => (
            <p key={i} className="error" role="alert">
              {e.row}-qator: {e.message}
            </p>
          ))}
          <div
            className="table-wrap"
            style={{ maxHeight: 300 }}
            tabIndex={0}
            role="region"
            aria-label="Import savollari"
          >
            <table>
              <caption className="sr-only">
                Tasdiqlashdan oldingi savollar ro‘yxati
              </caption>
              <thead>
                <tr>
                  <th scope="col">Qator</th>
                  <th scope="col">Savol</th>
                  <th scope="col">To‘g‘ri javob</th>
                  <th scope="col">Ball</th>
                  <th scope="col">Rasm</th>
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((r, i) => (
                  <tr key={i}>
                    <td>{r.source_row ?? i + 2}</td>
                    <td style={{ whiteSpace: "normal", minWidth: 160 }}>
                      {r.text}
                    </td>
                    <td>
                      {"ABCD"[r.correct_option]}: {r.options[r.correct_option]}
                    </td>
                    <td>{r.points}</td>
                    <td>
                      {r.image_base64 ? (
                        <img
                          src={"data:image/png;base64," + r.image_base64}
                          alt={`${r.source_row ?? i + 2}-qator rasmi`}
                          width={60}
                        />
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {confirmed ? (
            <p role="status">{preview.count} ta savol import qilindi.</p>
          ) : (
            <Button
              disabled={busy || preview.errors.length > 0 || !preview.count}
              onClick={async () => {
                setBusy(true);
                try {
                  await post("questions/import/confirm/", { id: preview.id });
                  setConfirmed(true);
                  onSaved();
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              Importni tasdiqlash
            </Button>
          )}
        </>
      )}
    </Modal>
  );
}
