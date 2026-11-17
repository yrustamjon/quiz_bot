import { useUnsavedChanges } from "../components/useUnsavedChanges";
import { useConfirmation } from "../components/ConfirmationProvider";
import type { Page, CommandResponse } from "../services/types";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, post } from "../services/api";
import { useAuth } from "../services/auth";
import { Button } from "../components/ui/button";
import { Modal } from "../components/ui/dialog";
import { Loading, Empty, ErrorState } from "../components/states";
const schema = z.object({
  full_name: z.string().min(3, "Ismni to‘liq kiriting."),
  username: z.string().min(3),
  email: z.email("Email noto‘g‘ri."),
  specialty: z.string().min(1),
});
export default function Teachers() {
  const confirmAction = useConfirmation();
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [active, setActive] = useState("");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<number>();
  const [secret, setSecret] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const c = useQueryClient();
  const f = useForm({ resolver: zodResolver(schema) });
  const q = useQuery({
    queryKey: ["teachers", search, page, active],
    queryFn: () =>
      api<Page<import("../services/api").User>>(
        `teachers/?search=${encodeURIComponent(search)}&page=${page}&is_active=${active}`,
      ),
    enabled: user?.role === "SUPER_ADMIN",
  });
  if (user?.role !== "SUPER_ADMIN")
    return <p role="alert">Bu sahifaga kirish huquqingiz yo‘q.</p>;
  useUnsavedChanges(open && f.formState.isDirty);
  async function action(id: number, name: string) {
    setBusy(true);
    setError("");
    try {
      const r = await post<CommandResponse>(`teachers/${id}/${name}/`);
      if (r.temporary_password) setSecret(r.temporary_password);
      c.invalidateQueries({ queryKey: ["teachers"] });
      setNotice("Amal bajarildi.");
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
          <div className="eyebrow">JAMOANI BOSHQARISH</div>
          <h1>O‘qituvchilar</h1>
          <p>Hisoblar va xavfsiz kirishni boshqaring.</p>
        </div>
        <Button
          onClick={async () => {
            setEditing(undefined);
            f.reset({ full_name: "", username: "", email: "", specialty: "" });
            setOpen(true);
          }}
        >
          O‘qituvchi yaratish
        </Button>
      </div>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      <section className="card">
        <div className="toolbar">
          <select
            aria-label="Hisob holati"
            value={active}
            onChange={(e) => {
              setActive(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Barcha hisoblar</option>
            <option value="true">Faol</option>
            <option value="false">Nofaol</option>
          </select>
          <input
            aria-label="O‘qituvchi qidirish"
            placeholder="Ism yoki login…"
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
        ) : q.data.results.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Ism</th>
                  <th>Login / Email</th>
                  <th>Fan</th>
                  <th>Testlar</th>
                  <th>Yaratilgan</th>
                  <th>Holat</th>
                  <th>Amallar</th>
                </tr>
              </thead>
              <tbody>
                {q.data.results.map((t) => (
                  <tr key={t.id}>
                    <td>{t.full_name}</td>
                    <td>
                      {t.username}
                      <p className="hint">{t.email}</p>
                    </td>
                    <td>{t.specialty}</td>
                    <td>{t.quiz_count}</td>
                    <td>
                      {new Date(t.created_at).toLocaleDateString("uz-UZ", {
                        timeZone: "Asia/Tashkent",
                      })}
                    </td>
                    <td>{t.is_active ? "Faol" : "Nofaol"}</td>
                    <td>
                      <div className="actions">
                        <Button
                          variant="outline"
                          onClick={async () => {
                            setEditing(t.id);
                            f.reset(t);
                            setOpen(true);
                          }}
                        >
                          Tahrirlash
                        </Button>
                        <Button
                          variant="outline"
                          disabled={busy}
                          onClick={async () => {
                            if (
                              await confirmAction(
                                t.is_active
                                  ? "Kirish bekor qilinadi. Hisobni o‘chirasizmi?"
                                  : "Hisob faollashtirilsinmi?",
                              )
                            )
                              action(
                                t.id,
                                t.is_active ? "deactivate" : "activate",
                              );
                          }}
                        >
                          {t.is_active ? "Nofaol qilish" : "Faollashtirish"}
                        </Button>
                        <Button
                          disabled={busy}
                          variant="outline"
                          onClick={async () => {
                            if (
                              await confirmAction(
                                "Yangi vaqtinchalik parol berilsinmi?",
                              )
                            )
                              action(t.id, "reset-password");
                          }}
                        >
                          Parolni yangilash
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty />
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
      <Modal
        open={open}
        onOpenChange={async (next) => {
          if (
            next ||
            !f.formState.isDirty ||
            (await confirmAction(
              "Saqlanmagan o‘qituvchi ma’lumotlarini yopasizmi?",
            ))
          )
            setOpen(next);
        }}
        title={editing ? "O‘qituvchini tahrirlash" : "O‘qituvchi yaratish"}
      >
        <form
          onSubmit={f.handleSubmit(async (v) => {
            setError("");
            try {
              const t = editing
                ? await api<import("../services/api").User & CommandResponse>(
                    `teachers/${editing}/`,
                    {
                      method: "PATCH",
                      body: JSON.stringify(v),
                    },
                  )
                : await post<import("../services/api").User & CommandResponse>(
                    "teachers/",
                    v,
                  );
              if (t.temporary_password) setSecret(t.temporary_password);
              setOpen(false);
              f.reset();
              c.invalidateQueries({ queryKey: ["teachers"] });
            } catch (e) {
              setError((e as Error).message);
            }
          })}
        >
          {[
            ["full_name", "Ism va familiya"],
            ["username", "Login"],
            ["email", "Email"],
            ["specialty", "Fan"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                {...f.register(key as keyof z.infer<typeof schema>)}
                type={key === "email" ? "email" : "text"}
                required
              />
              <small role="alert">
                {
                  f.formState.errors[key as keyof z.infer<typeof schema>]
                    ?.message
                }
              </small>
            </label>
          ))}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <Button disabled={f.formState.isSubmitting}>
            {editing ? "Saqlash" : "Yaratish"}
          </Button>
        </form>
      </Modal>
      <Modal
        open={!!secret}
        onOpenChange={(v) => {
          if (!v) setSecret("");
        }}
        title="Vaqtinchalik parol"
        description="Ushbu parol faqat bir marta ko‘rsatiladi. Uni o‘qituvchiga xavfsiz usulda yetkazing. 24 soatda muddati tugaydi."
      >
        <output
          style={{
            display: "block",
            padding: 20,
            overflowWrap: "anywhere",
            fontFamily: "monospace",
          }}
        >
          {secret}
        </output>
        <div className="actions">
          <Button
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(secret);
                setNotice("Parol nusxalandi.");
              } catch {
                setNotice(
                  "Avtomatik nusxalash ishlamadi; parolni qo‘lda belgilang.",
                );
              }
            }}
          >
            Nusxalash
          </Button>
          <Button variant="outline" onClick={() => setSecret("")}>
            Yopish
          </Button>
        </div>
      </Modal>
    </>
  );
}
