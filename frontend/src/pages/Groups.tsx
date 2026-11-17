import { useUnsavedChanges } from "../components/useUnsavedChanges";
import { useConfirmation } from "../components/ConfirmationProvider";
import type { Group, Student, Page } from "../services/types";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post } from "../services/api";
import { useAuth } from "../services/auth";
import { Loading, ErrorState, Empty } from "../components/states";
import { Modal } from "../components/ui/dialog";
import { Button } from "../components/ui/button";
const schema = z.object({
  name: z.string().trim().min(1, "Guruh nomini kiriting.").max(150),
});
export default function Groups() {
  const confirmAction = useConfirmation();
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<number>();
  const [members, setMembers] = useState<number[]>([]);
  const [initialMembers, setInitialMembers] = useState<number[]>([]);
  const [page, setPage] = useState(1);
  const [studentPage, setStudentPage] = useState(1);
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const c = useQueryClient();
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { name: "" },
  });
  const dirty =
    form.formState.isDirty ||
    JSON.stringify([...members].sort()) !==
      JSON.stringify([...initialMembers].sort());
  useUnsavedChanges(open && dirty);
  const q = useQuery({
    queryKey: ["groups", page],
    queryFn: () => api<Page<Group>>("groups/?page=" + page),
    enabled: user?.role === "SUPER_ADMIN",
  });
  const students = useQuery({
    queryKey: ["group-students", search, studentPage],
    queryFn: () =>
      api<Page<Student>>(
        `students/?search=${encodeURIComponent(search)}&page=${studentPage}`,
      ),
    enabled: open && user?.role === "SUPER_ADMIN",
  });
  if (user?.role !== "SUPER_ADMIN")
    return <p role="alert">Kirish huquqi yo‘q.</p>;
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Guruhlar</h1>
          <p>Guruh a’zoligi testlarga egalik ruxsatlarini o‘zgartirmaydi.</p>
        </div>
        <Button
          onClick={async () => {
            setEditing(undefined);
            setMembers([]);
            setInitialMembers([]);
            form.reset({ name: "" });
            setError("");
            setOpen(true);
          }}
        >
          Guruh yaratish
        </Button>
      </div>
      {error && !open && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      <section className="card padded">
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorState error={q.error} retry={() => q.refetch()} />
        ) : q.data.results.length ? (
          q.data.results.map((g) => (
            <div className="section-heading" key={g.id}>
              <div>
                <h2>{g.name}</h2>
                <p>{g.students.length} o‘quvchi</p>
              </div>
              <div className="actions">
                <Button
                  variant="outline"
                  onClick={async () => {
                    setEditing(g.id);
                    setMembers(g.students);
                    setInitialMembers(g.students);
                    form.reset({ name: g.name });
                    setError("");
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
                      !(await confirmAction(
                        "Guruh o‘chirilsinmi? O‘quvchi hisoblari saqlanadi.",
                      ))
                    )
                      return;
                    setBusy(true);
                    try {
                      await api("groups/" + g.id + "/", { method: "DELETE" });
                      c.invalidateQueries({ queryKey: ["groups"] });
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  O‘chirish
                </Button>
              </div>
            </div>
          ))
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
            !dirty ||
            (await confirmAction("Saqlanmagan guruhni yopasizmi?"))
          )
            setOpen(next);
        }}
        title={editing ? "Guruhni tahrirlash" : "Yangi guruh"}
      >
        <form
          onSubmit={form.handleSubmit(async (v) => {
            setError("");
            try {
              const body = { ...v, students: members };
              if (editing)
                await api("groups/" + editing + "/", {
                  method: "PATCH",
                  body: JSON.stringify(body),
                });
              else await post("groups/", body);
              c.invalidateQueries({ queryKey: ["groups"] });
              setOpen(false);
            } catch (e) {
              setError((e as Error).message);
            }
          })}
        >
          <label>
            Guruh nomi
            <input {...form.register("name")} required maxLength={150} />
            <small role="alert">{form.formState.errors.name?.message}</small>
          </label>
          <label>
            O‘quvchi qidirish
            <input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setStudentPage(1);
              }}
            />
          </label>
          <p>{members.length} a’zo tanlangan</p>
          {students.isPending ? (
            <Loading />
          ) : students.error ? (
            <ErrorState
              error={students.error}
              retry={() => students.refetch()}
            />
          ) : (
            students.data.results.map((s) => (
              <label
                key={s.id}
                style={{ display: "flex", alignItems: "center", gap: 10 }}
              >
                <input
                  type="checkbox"
                  checked={members.includes(s.id)}
                  style={{ width: 20, minHeight: 20 }}
                  onChange={(e) =>
                    setMembers(
                      e.target.checked
                        ? [...members, s.id]
                        : members.filter((id) => id !== s.id),
                    )
                  }
                />
                {s.full_name}
              </label>
            ))
          )}
          <div className="pagination">
            <Button
              type="button"
              variant="outline"
              disabled={!students.data?.previous}
              onClick={() => setStudentPage(studentPage - 1)}
            >
              Oldingi a’zolar
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={!students.data?.next}
              onClick={() => setStudentPage(studentPage + 1)}
            >
              Keyingi a’zolar
            </Button>
          </div>
          {error && (
            <p role="alert" className="notice error">
              {error}
            </p>
          )}
          <Button disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? "Saqlanmoqda…" : "Saqlash"}
          </Button>
        </form>
      </Modal>
    </>
  );
}
