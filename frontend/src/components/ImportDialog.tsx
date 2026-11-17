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
  const [preview, setPreview] = useState<any>();
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
      <label>
        Import fayli
        <input
          type="file"
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
                await api("questions/import/preview/", {
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
      </label>
      {busy && <p role="status">Tekshirilmoqda…</p>}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {preview && (
        <>
          <h3>{preview.count} ta savol</h3>
          {preview.errors.map((e: any, i: number) => (
            <p key={i} className="error" role="alert">
              {e.row}-qator: {e.message}
            </p>
          ))}
          <div style={{ maxHeight: 260, overflow: "auto" }}>
            {preview.rows.map((r: any, i: number) => (
              <div key={i} className="notice">
                <span>
                  {i + 1}. {r.text}
                </span>
                {r.image_base64 && (
                  <img
                    src={"data:image/png;base64," + r.image_base64}
                    alt={"Rasm " + (i + 1)}
                    width={60}
                  />
                )}
              </div>
            ))}
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
