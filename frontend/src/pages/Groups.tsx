import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post } from "../services/api";
import { useAuth } from "../services/auth";
import { Loading, ErrorState, Empty } from "../components/states";
import { Modal } from "../components/ui/dialog";
import { Button } from "../components/ui/button";
export default function Groups() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const c = useQueryClient();
  const q = useQuery({
    queryKey: ["groups"],
    queryFn: () => api("groups/"),
    enabled: user?.role === "SUPER_ADMIN",
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
        <Button onClick={() => setOpen(true)}>Guruh yaratish</Button>
      </div>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      <section className="card padded">
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorState error={q.error} />
        ) : q.data.results.length ? (
          q.data.results.map((g: any) => (
            <div className="section-heading" key={g.id}>
              <div>
                <h2>{g.name}</h2>
                <p>{g.students.length} o‘quvchi</p>
              </div>
              <Button
                variant="outline"
                disabled={busy}
                onClick={async () => {
                  if (
                    !confirm(
                      "Guruh o‘chirilsinmi? O‘quvchi hisoblari saqlanadi.",
                    )
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
          ))
        ) : (
          <Empty />
        )}
      </section>
      <Modal open={open} onOpenChange={setOpen} title="Yangi guruh">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              await post("groups/", {
                name: new FormData(e.currentTarget).get("name"),
                students: [],
              });
              c.invalidateQueries({ queryKey: ["groups"] });
              setOpen(false);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Guruh nomi
            <input name="name" required maxLength={150} />
          </label>
          <Button disabled={busy}>Saqlash</Button>
        </form>
      </Modal>
    </>
  );
}
