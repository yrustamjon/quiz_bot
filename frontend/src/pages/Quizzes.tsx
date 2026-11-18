import { useConfirmation } from "../components/ConfirmationProvider";
import { useUnsavedChanges } from "../components/useUnsavedChanges";
import { QuizActions } from "../components/QuizActions";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
const creationSchema = z.object({
  title: z.string().trim().min(1).max(200),
  subject: z.string().trim().min(1).max(100),
  duration: z.coerce.number().int().min(1).max(1440),
  count: z.coerce.number().int().min(1).max(500),
});
import { useAuth } from "../services/auth";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
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
  const { user } = useAuth();
  const confirmAction = useConfirmation();
  const navigate = useNavigate();
  const [urlParams, setUrlParams] = useSearchParams();
  const [subject, setSubject] = useState("");
  const [access, setAccess] = useState("");
  const [ordering, setOrdering] = useState("-created_at");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState(urlParams.get("status") || "");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(urlParams.has("create"));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const cache = useQueryClient();
  const form = useForm({
    resolver: zodResolver(creationSchema),
    defaultValues: { title: "", subject: "", duration: 30, count: 10 },
  });
  const allowNavigation = useUnsavedChanges(open && form.formState.isDirty);
  const q = useQuery({
    queryKey: ["quizzes", search, status, page, subject, access, ordering],
    queryFn: () =>
      api<{
        results: Quiz[];
        count: number;
        next: string | null;
        previous: string | null;
      }>(
        `quizzes/?search=${encodeURIComponent(search)}&status=${status}&page=${page}&subject=${encodeURIComponent(subject)}&access=${access}&ordering=${ordering}`,
      ),
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">TESTLARNI BOSHQARISH</div>
          <h1>{user?.role === "SUPER_ADMIN" ? "Testlar" : "Testlarim"}</h1>
          <p>Testlaringizni yarating, boshqaring va natijalarni kuzating.</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus size={18} />
          Yangi test
        </Button>
      </div>
      <section className="card">
        <div className="toolbar" style={{ flexWrap: "wrap" }}>
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
          <input
            aria-label="Fan filtri"
            placeholder="Fan nomi"
            value={subject}
            style={{ maxWidth: 180 }}
            onChange={(e) => {
              setSubject(e.target.value);
              setPage(1);
            }}
          />
          <select
            aria-label="Kirish turi"
            value={access}
            onChange={(e) => {
              setAccess(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Barcha kirish turlari</option>
            <option value="public">Ochiq</option>
            <option value="private">Kod bilan</option>
          </select>
          <select
            aria-label="Saralash"
            value={ordering}
            onChange={(e) => {
              setOrdering(e.target.value);
              setPage(1);
            }}
          >
            <option value="-created_at">Avval yangilari</option>
            <option value="created_at">Avval eskilari</option>
            <option value="title">Nomi bo‘yicha</option>
          </select>
          <Button
            variant="outline"
            onClick={() => {
              setSearch("");
              setStatus("");
              setSubject("");
              setAccess("");
              setOrdering("-created_at");
              setPage(1);
            }}
          >
            Filtrlarni tiklash
          </Button>
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
                  {user?.role === "SUPER_ADMIN" && <th>O‘qituvchi</th>}
                  <th>Kirish</th>
                  <th>Qatnashuvchilar</th>
                  <th>Yaratilgan</th>
                  <th>Savollar / vaqt</th>
                  <th>Holat</th>
                  <th>Amallar</th>
                </tr>
              </thead>
              <tbody>
                {q.data.results.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link
                        className="table-title"
                        aria-label={item.title}
                        to={"/quizzes/" + item.id}
                      >
                        <span className="mini-icon">
                          <BookOpen size={18} />
                        </span>
                        <span>
                          <strong>{item.title}</strong>
                          <span className="cell-subtitle">{item.subject}</span>
                        </span>
                      </Link>
                    </td>
                    {user?.role === "SUPER_ADMIN" && <td>{item.owner_name}</td>}
                    <td>{item.access === "public" ? "Ochiq" : "Kod bilan"}</td>
                    <td>{item.participants}</td>
                    <td>
                      {new Date(item.created_at).toLocaleDateString("uz-UZ", {
                        timeZone: "Asia/Tashkent",
                      })}
                    </td>
                    <td>
                      <strong>
                        {item.available_questions} / {item.question_count}
                      </strong>
                      <span className="cell-subtitle">
                        {item.duration_minutes} daqiqa
                      </span>
                    </td>
                    <td>
                      <span className={"badge " + item.status}>
                        {labels[item.status]}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <Link className="text-link" to={"/quizzes/" + item.id}>
                          Ochish <ArrowUpRight size={15} />
                        </Link>
                        <QuizActions quiz={item} />
                      </div>
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
        onOpenChange={async (v) => {
          if (
            !v &&
            form.formState.isDirty &&
            !(await confirmAction("Saqlanmagan testni yopasizmi?"))
          )
            return;
          setOpen(v);
          if (!v && urlParams.has("create")) {
            const next = new URLSearchParams(urlParams);
            next.delete("create");
            setUrlParams(next, { replace: true });
          }
        }}
        title="Yangi test"
        description="Qoralamani yarating. Keyingi bosqichda savollar va nashr sozlamalarini belgilang."
      >
        <form
          onSubmit={form.handleSubmit(async (values) => {
            setBusy(true);
            setError("");
            try {
              const created = await post<Quiz>("quizzes/", {
                title: values.title,
                subject: values.subject,
                duration_minutes: values.duration,
                question_count: values.count,
              });
              cache.invalidateQueries({ queryKey: ["quizzes"] });
              allowNavigation();
              form.reset();
              setOpen(false);
              navigate(`/quizzes/${created.id}`);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          })}
        >
          <label>
            Test nomi
            <input {...form.register("title")} required maxLength={200} />
          </label>
          <label>
            Fan
            <input {...form.register("subject")} required maxLength={100} />
          </label>
          <div className="two-col">
            <label>
              Davomiylik (daqiqa)
              <input
                type="number"
                {...form.register("duration")}
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
                {...form.register("count")}
                defaultValue={10}
                min={1}
                max={500}
                required
              />
            </label>
          </div>
          {Object.keys(form.formState.errors).length > 0 && (
            <p className="notice error" role="alert">
              Barcha maydonlarni to‘g‘ri to‘ldiring.
            </p>
          )}
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
