import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, Search, BookOpen, ArrowUpRight } from "lucide-react";
import { api, post, type Quiz } from "../services/api";
import { Button } from "../components/ui/button";
import { Loading, Empty, ErrorState } from "../components/states";
import { Modal } from "../components/ui/dialog";
const labels: Record<string, string> = {
  draft: "Qoralama",
  published: "Faol",
  closed: "Yopilgan",
  archived: "Arxivlangan",
};
export default function Quizzes() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const cache = useQueryClient();
  const q = useQuery({
    queryKey: ["quizzes", search, status, page],
    queryFn: () =>
      api<{
        results: Quiz[];
        count: number;
        next: string | null;
        previous: string | null;
      }>(
        `quizzes/?search=${encodeURIComponent(search)}&status=${status}&page=${page}`,
      ),
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">TESTLARNI BOSHQARISH</div>
          <h1>Testlarim</h1>
          <p>Testlaringizni yarating, boshqaring va natijalarni kuzating.</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus size={18} />
          Yangi test
        </Button>
      </div>
      <section className="card">
        <div className="toolbar">
          <div className="search">
            <Search size={18} />
            <input
              aria-label="Test qidirish"
              placeholder="Test nomi bo‘yicha qidirish…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <select
            aria-label="Test holati"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Barcha holatlar</option>
            {Object.entries(labels).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <span className="hint">{q.data?.count ?? 0} ta test</span>
        </div>
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorState error={q.error} retry={() => q.refetch()} />
        ) : !q.data?.results.length ? (
          <Empty
            text={
              search
                ? "Qidiruvga mos test topilmadi."
                : "Birinchi testingizni yarating."
            }
          />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Test nomi</th>
                  <th>Fan</th>
                  <th>Savollar</th>
                  <th>Davomiylik</th>
                  <th>Holat</th>
                  <th>Amallar</th>
                </tr>
              </thead>
              <tbody>
                {q.data.results.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link className="table-title" to={"/quizzes/" + item.id}>
                        <span className="mini-icon">
                          <BookOpen size={18} />
                        </span>
                        {item.title}
                      </Link>
                    </td>
                    <td>{item.subject}</td>
                    <td>
                      {item.available_questions} / {item.question_count}
                    </td>
                    <td>{item.duration_minutes} daqiqa</td>
                    <td>
                      <span className={"badge " + item.status}>
                        {labels[item.status]}
                      </span>
                    </td>
                    <td>
                      <Link className="text-link" to={"/quizzes/" + item.id}>
                        Ochish <ArrowUpRight size={15} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
        onOpenChange={setOpen}
        title="Yangi test"
        description="Qoralamani yarating. Keyingi bosqichda savollar va nashr sozlamalarini belgilang."
      >
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            const d = new FormData(e.currentTarget);
            try {
              await post("quizzes/", {
                title: d.get("title"),
                subject: d.get("subject"),
                duration_minutes: Number(d.get("duration")),
                question_count: Number(d.get("count")),
              });
              cache.invalidateQueries({ queryKey: ["quizzes"] });
              setOpen(false);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Test nomi
            <input name="title" required maxLength={200} />
          </label>
          <label>
            Fan
            <input name="subject" required maxLength={100} />
          </label>
          <div className="two-col">
            <label>
              Davomiylik (daqiqa)
              <input
                type="number"
                name="duration"
                defaultValue={30}
                min={1}
                max={1440}
                required
              />
            </label>
            <label>
              Savollar soni
              <input
                type="number"
                name="count"
                defaultValue={10}
                min={1}
                max={500}
                required
              />
            </label>
          </div>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <Button disabled={busy}>
            {busy ? "Saqlanmoqda…" : "Qoralamani yaratish"}
          </Button>
        </form>
      </Modal>
    </>
  );
}
