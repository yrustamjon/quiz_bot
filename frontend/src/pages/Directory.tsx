import { useState } from "react";
import { QuestionEditor } from "../components/QuestionEditor";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { Loading, ErrorState, Empty } from "../components/states";
import { Button } from "../components/ui/button";
export default function Directory({
  kind,
}: {
  kind: "students" | "questions" | "teachers";
}) {
  const [search, setSearch] = useState("");
  const cache = useQueryClient();
  const [editor, setEditor] = useState(false);
  const [editing, setEditing] = useState<any>();
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const titles = {
    students: "O‘quvchilar",
    questions: "Savollar",
    teachers: "O‘qituvchilar",
  };
  const q = useQuery({
    queryKey: [kind, search, page],
    queryFn: () =>
      api(`${kind}/?search=${encodeURIComponent(search)}&page=${page}`),
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">MA’LUMOTLAR</div>
          <h1>{titles[kind]}</h1>
          <p>Faqat sizga ruxsat berilgan ma’lumotlar ko‘rsatiladi.</p>
        </div>
        {kind === "questions" && (
          <Button
            onClick={() => {
              setEditing(undefined);
              setEditor(true);
            }}
          >
            Yangi savol
          </Button>
        )}
      </div>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <section className="card">
        <div className="toolbar">
          <input
            aria-label="Qidirish"
            placeholder="Qidirish…"
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
        ) : q.data?.results.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{kind === "questions" ? "Savol" : "Ism"}</th>
                  <th>{kind === "questions" ? "Fan" : "Login"}</th>
                  {kind === "questions" && <th>Amallar</th>}
                </tr>
              </thead>
              <tbody>
                {q.data.results.map((x: any) => (
                  <tr key={x.id}>
                    <td>{x.full_name || x.text || x.username}</td>
                    <td>
                      {x.subject || x.username || x.telegram_username || "—"}
                    </td>
                    {kind === "questions" && (
                      <td>
                        <div className="actions">
                          <Button
                            variant="outline"
                            onClick={() => {
                              setEditing(x);
                              setEditor(true);
                            }}
                          >
                            Tahrirlash
                          </Button>
                          <Button
                            variant="outline"
                            onClick={async () => {
                              if (!confirm("Savol o‘chirilsinmi?")) return;
                              try {
                                await api("questions/" + x.id + "/", {
                                  method: "DELETE",
                                });
                                cache.invalidateQueries({
                                  queryKey: ["questions"],
                                });
                              } catch (e) {
                                setError((e as Error).message);
                              }
                            }}
                          >
                            O‘chirish
                          </Button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            text={search ? "Qidiruvga mos ma’lumot topilmadi." : undefined}
          />
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
      {editor && (
        <QuestionEditor
          key={editing?.id || "new"}
          question={editing}
          open={editor}
          onClose={() => setEditor(false)}
          onSaved={() => {
            cache.invalidateQueries({ queryKey: ["questions"] });
          }}
        />
      )}
    </>
  );
}
