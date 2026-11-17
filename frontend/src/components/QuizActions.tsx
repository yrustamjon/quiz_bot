import { useState } from "react";
import * as Dropdown from "@radix-ui/react-dropdown-menu";
import { MoreHorizontal } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { api, post, type Quiz } from "../services/api";
import { ConfirmDialog } from "./ConfirmDialog";
import { Modal } from "./ui/dialog";
import { Button } from "./ui/button";
const commands: Record<string, string> = {
  publish: "Testni nashr qilish",
  close: "Testni yopish",
  archive: "Testni arxivlash",
  delete: "Qoralamani o‘chirish",
};
export function QuizActions({ quiz }: { quiz: Quiz }) {
  const [pending, setPending] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [code, setCode] = useState<{
    code: string;
    expires_at: string | null;
  }>();
  const cache = useQueryClient();
  const navigate = useNavigate();
  async function run(command: string) {
    setBusy(true);
    setError("");
    try {
      if (command === "delete")
        await api(`quizzes/${quiz.id}/`, { method: "DELETE" });
      else await post(`quizzes/${quiz.id}/${command}/`);
      cache.invalidateQueries({ queryKey: ["quizzes"] });
      cache.invalidateQueries({ queryKey: ["quiz", String(quiz.id)] });
      setPending("");
      if (command === "delete") navigate("/quizzes");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Dropdown.Root>
        <Dropdown.Trigger
          className="icon"
          disabled={busy}
          aria-label={quiz.title + ": amallar"}
        >
          <MoreHorizontal size={18} />
        </Dropdown.Trigger>
        <Dropdown.Portal>
          <Dropdown.Content className="account-menu" align="end" sideOffset={8}>
            <Dropdown.Item asChild>
              <Link to={`/quizzes/${quiz.id}`}>Ko‘rish / tahrirlash</Link>
            </Dropdown.Item>
            <Dropdown.Item onSelect={() => run("duplicate")}>
              Nusxa yaratish
            </Dropdown.Item>
            {quiz.status === "draft" && (
              <Dropdown.Item onSelect={() => setPending("publish")}>
                Nashr qilish
              </Dropdown.Item>
            )}
            {quiz.status === "published" && (
              <Dropdown.Item onSelect={() => setPending("close")}>
                Yopish
              </Dropdown.Item>
            )}
            {["draft", "closed"].includes(quiz.status) && (
              <Dropdown.Item onSelect={() => setPending("archive")}>
                Arxivlash
              </Dropdown.Item>
            )}
            <Dropdown.Item asChild>
              <Link to={`/results?quiz=${quiz.id}`}>Natijalar</Link>
            </Dropdown.Item>
            {quiz.access === "private" && (
              <Dropdown.Item
                onSelect={async () => {
                  setBusy(true);
                  setError("");
                  try {
                    setCode(
                      await api<{ code: string; expires_at: string | null }>(
                        `quizzes/${quiz.id}/access-code/`,
                      ),
                    );
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Kirish kodi
              </Dropdown.Item>
            )}
            {quiz.status === "draft" && (
              <Dropdown.Item onSelect={() => setPending("delete")}>
                O‘chirish
              </Dropdown.Item>
            )}
          </Dropdown.Content>
        </Dropdown.Portal>
      </Dropdown.Root>
      <ConfirmDialog
        open={!!pending}
        title={commands[pending] || "Amalni tasdiqlash"}
        description={
          pending === "delete"
            ? "Qatnashuvchisiz qoralama o‘chiriladi. Bu amalni qaytarib bo‘lmaydi."
            : `«${quiz.title}» uchun ushbu amalni tasdiqlaysizmi?`
        }
        busy={busy}
        onCancel={() => setPending("")}
        onConfirm={() => run(pending)}
      />
      <Modal
        open={!!code}
        onOpenChange={(v) => {
          if (!v) setCode(undefined);
        }}
        title="Testga kirish kodi"
        description="Kodni faqat qatnashuvchilarga xavfsiz ulashing."
      >
        {code && (
          <>
            <output
              style={{
                display: "block",
                padding: 20,
                fontSize: 24,
                letterSpacing: 2,
              }}
            >
              {code.code}
            </output>
            <p>
              {code.expires_at
                ? "Amal qilish muddati: " +
                  new Date(code.expires_at).toLocaleString("uz-UZ", {
                    timeZone: "Asia/Tashkent",
                  })
                : "Alohida amal qilish muddati belgilanmagan."}
            </p>
            <Button
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  const result = await post<{ code: string }>(
                    `quizzes/${quiz.id}/regenerate-code/`,
                  );
                  setCode({ ...code, code: result.code });
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              Yangi kod yaratish
            </Button>
          </>
        )}
      </Modal>
      <Modal
        open={!!error}
        onOpenChange={(v) => {
          if (!v) setError("");
        }}
        title="Amal bajarilmadi"
        description={error}
      >
        <Button variant="outline" onClick={() => setError("")}>
          Yopish
        </Button>
      </Modal>
    </>
  );
}
