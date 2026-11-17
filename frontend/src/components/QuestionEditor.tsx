import { useConfirmation } from "./ConfirmationProvider";
import { FileUpload } from "./FileUpload";
import type { Question } from "../services/types";
import { useUnsavedChanges } from "./useUnsavedChanges";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "../services/api";
import { Modal } from "./ui/dialog";
import { Button } from "./ui/button";
const schema = z.object({
  text: z.string().min(1, "Savolni kiriting."),
  a: z.string().min(1),
  b: z.string().min(1),
  c: z.string().min(1),
  d: z.string().min(1),
  correct: z.coerce.number().min(0).max(3),
  points: z.coerce.number().positive().max(999999),
});
export function QuestionEditor({
  open,
  onClose,
  onSaved,
  question,
}: {
  open: boolean;
  onClose: () => void;
  onSaved: (id: number) => Promise<void> | void;
  question?: Question;
}) {
  const confirmAction = useConfirmation();
  const [error, setError] = useState("");
  const [image, setImage] = useState<File>();
  const [removeImage, setRemoveImage] = useState(false);
  const [preview, setPreview] = useState<string>();
  const f = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      text: question?.text || "",
      a: question?.options?.[0] || "",
      b: question?.options?.[1] || "",
      c: question?.options?.[2] || "",
      d: question?.options?.[3] || "",
      correct: question?.correct_option ?? 0,
      points: question?.points ?? 1,
    },
  });
  const hasChanges = f.formState.isDirty || !!image || removeImage;
  useUnsavedChanges(open && hasChanges);
  return (
    <Modal
      open={open}
      onOpenChange={async (v) => {
        if (
          !v &&
          (!hasChanges ||
            (await confirmAction("Saqlanmagan savolni yopasizmi?")))
        )
          onClose();
      }}
      title={question ? "Savolni tahrirlash" : "Yangi savol"}
    >
      <form
        onSubmit={f.handleSubmit(async (v) => {
          setError("");
          try {
            const body = {
              text: v.text,
              options: [v.a, v.b, v.c, v.d],
              correct_option: v.correct,
              points: v.points,
              remove_image: removeImage,
            };
            let payload: string | FormData = JSON.stringify(body);
            if (image) {
              const multipart = new FormData();
              for (const [key, value] of Object.entries(body)) {
                multipart.append(
                  key,
                  Array.isArray(value) ? JSON.stringify(value) : String(value),
                );
              }
              multipart.append("image", image);
              payload = multipart;
            }
            const q = await api<Question>(
              question ? `questions/${question.id}/` : "questions/",
              {
                method: question ? "PATCH" : "POST",
                body: payload,
              },
            );
            await onSaved(q.id);
            if (preview) URL.revokeObjectURL(preview);
            f.reset({
              text: "",
              a: "",
              b: "",
              c: "",
              d: "",
              correct: 0,
              points: 1,
            });
            setImage(undefined);
            setPreview(undefined);
            setRemoveImage(false);
            onClose();
          } catch (e) {
            setError((e as Error).message);
          }
        })}
      >
        <label>
          Savol matni
          <textarea {...f.register("text")} required />
        </label>
        {(["a", "b", "c", "d"] as const).map((name, i) => (
          <label key={name}>
            {"ABCD"[i]} variant
            <input {...f.register(name)} required />
          </label>
        ))}
        <fieldset>
          <legend>To‘g‘ri javob</legend>
          <div className="actions">
            {[0, 1, 2, 3].map((i) => (
              <label
                key={i}
                style={{ display: "flex", gap: 8, alignItems: "center" }}
              >
                <input
                  type="radio"
                  value={i}
                  {...f.register("correct")}
                  style={{ width: 20, minHeight: 20 }}
                />
                {"ABCD"[i]}
              </label>
            ))}
          </div>
        </fieldset>
        <label>
          Ball
          <input
            type="number"
            min="0.01"
            step="0.01"
            {...f.register("points")}
            required
          />
        </label>
        <FileUpload
          label="Rasm (PNG/JPEG/WebP, 5 MB gacha)"

          accept="image/png,image/jpeg,image/webp"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            if (file.size > 5 * 1024 * 1024) {
              setError("Rasm 5 MB dan oshmasin.");
              return;
            }
            if (preview) URL.revokeObjectURL(preview);
            setRemoveImage(false);
            setImage(file);
            setPreview(URL.createObjectURL(file));
          }}
        />
        {(preview || (!removeImage && question?.image_url)) && (
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              if (preview) URL.revokeObjectURL(preview);
              setPreview(undefined);
              setImage(undefined);
              setRemoveImage(true);
            }}
          >
            Rasmni olib tashlash
          </Button>
        )}
        {(preview || (!removeImage && question?.image_url)) && (
          <img
            src={preview || question?.image_url || undefined}
            alt="Yuklanadigan rasm"
            style={{ maxWidth: "100%", maxHeight: 160 }}
          />
        )}
        {Object.keys(f.formState.errors).length > 0 && (
          <p role="alert" className="error">
            Barcha maydonlarni to‘g‘ri to‘ldiring.
          </p>
        )}
        {error && (
          <p role="alert" className="notice error">
            {error}
          </p>
        )}
        <div className="actions">
          <Button disabled={f.formState.isSubmitting}>Saqlash</Button>
          <Button
            type="button"
            variant="outline"
            onClick={async () => {
              if (
                !hasChanges ||
                (await confirmAction("Saqlanmagan savolni yopasizmi?"))
              )
                onClose();
            }}
          >
            Bekor qilish
          </Button>
        </div>
      </form>
    </Modal>
  );
}
