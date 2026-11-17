import { formatPercent } from "../services/labels";
import { ImportChooser } from "../components/ImportChooser";
import type { Dashboard } from "../services/types";
import { statusLabel } from "../services/labels";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  BookOpen,
  Users,
  CheckCircle,
  ChartNoAxesCombined,
  ArrowUpRight,
  Plus,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { Button } from "../components/ui/button";
import { Loading, Empty, ErrorState } from "../components/states";
export default function Dashboard() {
  const [importOpen, setImportOpen] = useState(false);
  const [days, setDays] = useState("30");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const { user } = useAuth();
  const q = useQuery({
    queryKey: ["dashboard", days, start, end],
    queryFn: () =>
      api<Dashboard>(
        `dashboard/summary/?days=${days}&start=${start}&end=${end}`,
      ),
  });
  const d = q.data!;
  const stats = [
    { title: "Jami testlar", value: d?.quizzes, Icon: BookOpen },
    { title: "Faol testlar", value: d?.published, Icon: ChartNoAxesCombined },
    { title: "Qatnashuvchilar", value: d?.participants, Icon: Users },
    { title: "Yakunlangan urinishlar", value: d?.completed, Icon: CheckCircle },
    {
      title: "O‘rtacha natija",
      value: formatPercent(d?.average || 0) + "%",
      Icon: ChartNoAxesCombined,
    },
  ];
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">BUGUNGI IMKONIYATLAR</div>
          <h1>
            Xush kelibsiz, {user?.full_name?.split(" ")[0] || user?.username}
          </h1>
          <p>Ta’lim jarayoningiz va testlaringiz haqida qisqacha ma’lumot.</p>
        </div>
        <div className="actions">
          <Button asChild>
            <Link to="/quizzes?create=1">
              <Plus size={18} />
              Test yaratish
            </Link>
          </Button>
          <Button variant="outline" onClick={() => setImportOpen(true)}>
            Excel importi
          </Button>
        </div>
      </div>
      <div className="section-heading">
        <span className="hint">KO‘RSATKICHLAR</span>
        <select
          style={{ width: 170 }}
          aria-label="Hisobot davri"
          value={days}
          onChange={(e) => setDays(e.target.value)}
        >
          <option value="1">Bugun</option>
          <option value="7">Oxirgi 7 kun</option>
          <option value="30">Oxirgi 30 kun</option>
          <option value="90">Oxirgi 90 kun</option>
        </select>
      </div>
      <div
        className="toolbar report-filters dashboard-filters"
        style={{ marginBottom: 20 }}
      >
        <label>
          Sanadan
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          Sanagacha
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        {(start || end) && (
          <Button
            variant="outline"
            onClick={() => {
              setStart("");
              setEnd("");
            }}
          >
            Davrni tiklash
          </Button>
        )}
      </div>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorState error={q.error} retry={() => q.refetch()} />
      ) : (
        <>
          <div className="stat-grid primary-five">
            {stats.map(({ title, value, Icon }) => (
              <section className="card stat" key={title}>
                <div className="stat-top">
                  <span>{title}</span>
                  <Icon size={18} />
                </div>
                <strong>{value}</strong>
                <small>Haqiqiy ma’lumotlar asosida</small>
              </section>
            ))}
          </div>
          <div
            hidden={user?.role !== "SUPER_ADMIN"}
            className="stat-grid secondary-three"
          >
            {user?.role === "SUPER_ADMIN" && (
              <>
                <section className="card stat">
                  <p>O‘qituvchilar</p>
                  <strong>{d.teachers}</strong>
                  <small>{d.active_teachers} faol</small>
                </section>
                <section className="card stat">
                  <p>Ro‘yxatdagi o‘quvchilar</p>
                  <strong>{d.students}</strong>
                </section>
                <section className="card stat">
                  <p>Jami urinishlar</p>
                  <strong>{d.attempts}</strong>
                </section>
              </>
            )}
          </div>
          <div className="two-col">
            <section className="card padded">
              <div className="section-heading">
                <h2>Ishtirok faolligi</h2>
                <span className="hint">{days} kun</span>
              </div>
              <p className="hint">Kunlar bo‘yicha imtihon urinishlari</p>
              {d.activity.length ? (
                <div
                  className="chart"
                  role="img"
                  aria-label="Kunlik urinishlar grafigi"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={d.activity}>
                      <CartesianGrid stroke="var(--border)" vertical={false} />
                      <XAxis
                        dataKey="date"
                        stroke="var(--muted)"
                        fontSize={11}
                      />
                      <YAxis
                        allowDecimals={false}
                        stroke="var(--muted)"
                        fontSize={11}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "var(--surface)",
                          borderColor: "var(--border)",
                          color: "var(--text)",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="attempts"
                        name="Urinishlar"
                        stroke="var(--primary)"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <Empty text="Faollik hali qayd etilmagan." />
              )}
            </section>
            <section className="card padded">
              <div className="section-heading">
                <h2>So‘nggi testlar</h2>
                <Link className="text-link" to="/quizzes">
                  Barchasi
                  <ArrowUpRight size={15} />
                </Link>
              </div>
              {d.recent_quizzes.length ? (
                d.recent_quizzes.map((x) => (
                  <Link
                    key={x.id}
                    to={"/quizzes/" + x.id}
                    className="section-heading"
                  >
                    <div>
                      <strong>{x.title}</strong>
                      <p className="hint">{x.subject}</p>
                    </div>
                    <ArrowUpRight size={16} />
                  </Link>
                ))
              ) : (
                <Empty text="Birinchi testdan boshlang." />
              )}
            </section>
          </div>
          <div className="two-col" style={{ marginTop: 24 }}>
            <section className="card padded">
              <h2>Testlar holati</h2>
              {d.status_distribution?.length ? (
                d.status_distribution.map((row) => (
                  <div key={row.status} style={{ marginTop: 16 }}>
                    <div className="section-heading">
                      <span>{statusLabel[row.status]}</span>
                      <strong>{row.count}</strong>
                    </div>
                    <progress
                      aria-label={statusLabel[row.status]}
                      value={row.count}
                      max={d.quizzes || 1}
                      style={{ width: "100%", accentColor: "var(--primary)" }}
                    />
                  </div>
                ))
              ) : (
                <Empty />
              )}
            </section>
            <section className="card padded">
              <h2>Eng faol testlar</h2>
              {d.most_active?.length ? (
                d.most_active.map((row) => (
                  <div
                    className="section-heading"
                    style={{ marginTop: 16 }}
                    key={row.quiz_id}
                  >
                    <Link className="text-link" to={"/quizzes/" + row.quiz_id}>
                      {row.quiz__title}
                    </Link>
                    <strong>{row.count}</strong>
                  </div>
                ))
              ) : (
                <Empty />
              )}
            </section>
          </div>
          <section className="card padded" style={{ marginTop: 24 }}>
            <div className="section-heading">
              <h2>So‘nggi urinishlar</h2>
              <Link className="text-link" to="/results">
                Barcha natijalar
              </Link>
            </div>
            {d.recent_attempts?.length ? (
              d.recent_attempts.map((a) => (
                <div className="section-heading" key={a.id}>
                  <div>
                    <strong>{a.student_name}</strong>
                    <p>{a.quiz_title}</p>
                  </div>
                  <span>{formatPercent(a.percentage)}%</span>
                </div>
              ))
            ) : (
              <Empty text="Hali urinishlar yo‘q." />
            )}
          </section>
          <section className="card padded" style={{ marginTop: 24 }}>
            <div className="section-heading">
              <div>
                <h2>Bilimni baholashga tayyormisiz?</h2>
                <p className="hint">
                  Test yarating, savollarni kiriting va o‘quvchilaringiz bilan
                  ulashing.
                </p>
              </div>
              <Link className="text-link" to="/quizzes">
                Testlarga o‘tish <ArrowUpRight size={16} />
              </Link>
            </div>
          </section>
        </>
      )}
      <ImportChooser open={importOpen} onClose={() => setImportOpen(false)} />
    </>
  );
}
