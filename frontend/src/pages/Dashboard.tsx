import { lazy, Suspense, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowUpRight,
  BookOpen,
  CalendarDays,
  CheckCircle,
  ChartNoAxesCombined,
  FileSpreadsheet,
  Plus,
  Users,
  Sparkles,
} from "lucide-react";
import { ImportChooser } from "../components/ImportChooser";
import { Button } from "../components/ui/button";
import { Loading, Empty, ErrorState } from "../components/states";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { formatPercent, statusLabel } from "../services/labels";
import type { Dashboard as DashboardData } from "../services/types";
const ActivityChart = lazy(() => import("../components/ActivityChart"));
const periods: Record<string, string> = {
  "1": "Bugun",
  "7": "Oxirgi 7 kun",
  "30": "Oxirgi 30 kun",
  "90": "Oxirgi 90 kun",
};
export default function Dashboard() {
  const { user } = useAuth();
  const [importOpen, setImportOpen] = useState(false);
  const [days, setDays] = useState("30");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const q = useQuery({
    queryKey: ["dashboard", days, start, end],
    queryFn: () =>
      api<DashboardData>(
        `dashboard/summary/?days=${days}&start=${start}&end=${end}`,
      ),
  });
  const d = q.data!;
  const stats = [
    {
      title: "Jami testlar",
      value: d?.quizzes,
      Icon: BookOpen,
      tone: "indigo",
      hint: "Testlar kutubxonangiz",
    },
    {
      title: "Faol testlar",
      value: d?.published,
      Icon: ChartNoAxesCombined,
      tone: "green",
      hint: "Qatnashish uchun ochiq",
    },
    {
      title: "Qatnashuvchilar",
      value: d?.participants,
      Icon: Users,
      tone: "blue",
      hint: "Tanlangan davrda",
    },
    {
      title: "Yakunlangan urinishlar",
      value: d?.completed,
      Icon: CheckCircle,
      tone: "amber",
      hint: "Natijasi saqlangan",
    },
    {
      title: "O‘rtacha natija",
      value: formatPercent(d?.average) + "%",
      Icon: ChartNoAxesCombined,
      tone: "purple",
      hint: "Yakunlangan urinishlar",
    },
  ];
  const period = start || end ? "Tanlangan sana oralig‘i" : periods[days];
  return (
    <>
      <section className="dashboard-hero">
        <div className="hero-copy">
          <div className="hero-kicker">
            <span className="hero-dot" /> SIZNING ISH MAYDONINGIZ
          </div>
          <h1>
            Xush kelibsiz, {user?.full_name?.split(" ")[0] || user?.username}
          </h1>
          <p>
            Yaxshi test. Aniq natija. O‘quvchilaringiz uchun navbatdagi qadamni
            yarating.
          </p>
          <div className="hero-actions">
            <Button asChild>
              <Link to="/quizzes?create=1">
                <Plus size={17} />
                Test yaratish
              </Link>
            </Button>
            <Button variant="outline" onClick={() => setImportOpen(true)}>
              <FileSpreadsheet size={17} />
              Excel importi
            </Button>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="hero-ring ring-one" />
          <div className="hero-ring ring-two" />
          <div className="hero-symbol">
            <BookOpen size={42} strokeWidth={1.4} />
            <span>
              <Sparkles size={17} />
            </span>
          </div>
          <span className="hero-art-caption">O‘rgating. Sinang. Kuzating.</span>
        </div>
      </section>
      <div className="dashboard-period">
        <div>
          <h2>Umumiy ko‘rsatkichlar</h2>
          <p>{period}</p>
        </div>
        <div className="period-actions">
          <label className="sr-only" htmlFor="dashboard-period">
            Hisobot davri
          </label>
          <select
            id="dashboard-period"
            aria-label="Hisobot davri"
            value={days}
            onChange={(e) => {
              setDays(e.target.value);
              setStart("");
              setEnd("");
            }}
          >
            {Object.entries(periods).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <details className="date-range">
            <summary>
              <CalendarDays size={16} />
              Sana oralig‘i
            </summary>
            <div className="date-range-panel">
              <label>
                Sanadan
                <input
                  type="date"
                  value={start}
                  max={end || undefined}
                  onChange={(e) => setStart(e.target.value)}
                />
              </label>
              <label>
                Sanagacha
                <input
                  type="date"
                  value={end}
                  min={start || undefined}
                  onChange={(e) => setEnd(e.target.value)}
                />
              </label>
              <Button
                variant="outline"
                disabled={!start && !end}
                onClick={() => {
                  setStart("");
                  setEnd("");
                }}
              >
                Davrni tiklash
              </Button>
            </div>
          </details>
        </div>
      </div>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorState error={q.error} retry={() => q.refetch()} />
      ) : (
        <>
          <div className="stat-grid primary-five">
            {stats.map(({ title, value, Icon, tone, hint }) => (
              <section className={"card stat stat-" + tone} key={title}>
                <div className="stat-top">
                  <span>{title}</span>
                  <span className="stat-icon">
                    <Icon size={18} />
                  </span>
                </div>
                <strong>{value}</strong>
                <small>{hint}</small>
              </section>
            ))}
          </div>
          {user?.role === "SUPER_ADMIN" && (
            <div className="admin-overview">
              <span>
                <Users size={16} />
                <strong>{d.teachers}</strong> o‘qituvchi{" "}
                <span className="admin-overview-note">
                  ({d.active_teachers} faol)
                </span>
              </span>
              <span>
                <strong>{d.students}</strong> ro‘yxatdagi o‘quvchi
              </span>
              <span>
                <strong>{d.attempts}</strong> jami urinish
              </span>
            </div>
          )}
          <div className="dashboard-main-grid">
            <section className="card dashboard-activity">
              <div className="section-heading">
                <div>
                  <h2>Ishtirok faolligi</h2>
                  <p className="hint">Kunlar bo‘yicha imtihon urinishlari</p>
                </div>
                <span className="period-pill">{period}</span>
              </div>
              <div className="activity-total">
                <strong>{d.attempts}</strong>
                <span>urinish qayd etilgan</span>
              </div>
              {d.activity.length ? (
                <Suspense fallback={<Loading />}>
                  <ActivityChart data={d.activity} />
                </Suspense>
              ) : (
                <Empty text="Faollik hali qayd etilmagan." />
              )}
              <div className="chart-footer">
                <span className="legend-dot" /> Imtihonni boshlaganlar
                <Link to="/results" className="text-link">
                  Natijalarni ko‘rish <ArrowUpRight size={14} />
                </Link>
              </div>
            </section>
            <section className="card recent-tests">
              <div className="section-heading">
                <h2>So‘nggi testlar</h2>
                <Link to="/quizzes" className="text-link">
                  Barchasi <ArrowUpRight size={14} />
                </Link>
              </div>
              {d.recent_quizzes.length ? (
                d.recent_quizzes.map((quiz, index) => (
                  <Link
                    className="recent-quiz"
                    to={"/quizzes/" + quiz.id}
                    key={quiz.id}
                  >
                    <span className={"quiz-tile tile-" + (index % 3)}>
                      <BookOpen size={19} />
                    </span>
                    <div>
                      <strong>{quiz.title}</strong>
                      <p>{quiz.subject}</p>
                      <span className={"badge " + quiz.status}>
                        {statusLabel[quiz.status]}
                      </span>
                    </div>
                    <ArrowUpRight size={16} className="row-arrow" />
                  </Link>
                ))
              ) : (
                <Empty text="Birinchi testdan boshlang." />
              )}
              <Link className="dashboard-inline-action" to="/quizzes?create=1">
                <Plus size={16} /> Yangi test yaratish
              </Link>
            </section>
          </div>
          <div className="dashboard-bottom-grid">
            <section className="card padded">
              <div className="section-heading">
                <h2>Testlar holati</h2>
                <BookOpen size={16} className="muted-icon" />
              </div>
              <div className="status-total">
                <strong>{d.quizzes}</strong>
                <span>jami test</span>
              </div>
              {d.status_distribution.length ? (
                <>
                  <div className="status-track" aria-hidden="true">
                    {d.status_distribution.map((row) => (
                      <span
                        className={"status-segment " + row.status}
                        style={{
                          width: `${(row.count / (d.quizzes || 1)) * 100}%`,
                        }}
                        key={row.status}
                      />
                    ))}
                  </div>
                  <div className="status-legend">
                    {d.status_distribution.map((row) => (
                      <Link
                        to={"/quizzes?status=" + row.status}
                        key={row.status}
                      >
                        <span className={"status-dot " + row.status} />
                        {statusLabel[row.status]}
                        <strong>{row.count}</strong>
                      </Link>
                    ))}
                  </div>
                </>
              ) : (
                <Empty text="Hali test yo‘q." />
              )}
            </section>
            <section className="card padded">
              <div className="section-heading">
                <h2>Eng faol testlar</h2>
                <ChartNoAxesCombined size={16} className="muted-icon" />
              </div>
              {d.most_active.length ? (
                d.most_active.map((row, i) => (
                  <div className="active-quiz" key={row.quiz_id}>
                    <span className="list-position">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <div>
                      <Link to={"/quizzes/" + row.quiz_id}>
                        {row.quiz__title}
                      </Link>
                      <div className="activity-track" aria-hidden="true">
                        <span
                          style={{
                            width: `${(row.count / (d.most_active[0].count || 1)) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                    <strong>
                      {row.count}
                      <small>urinish</small>
                    </strong>
                  </div>
                ))
              ) : (
                <Empty text="Birinchi natijadan keyin ko‘rinadi." />
              )}
            </section>
            <section className="card padded">
              <div className="section-heading">
                <h2>So‘nggi urinishlar</h2>
                <Link className="text-link" to="/results">
                  Barchasi <ArrowUpRight size={14} />
                </Link>
              </div>
              {d.recent_attempts.length ? (
                d.recent_attempts.map((attempt) => (
                  <Link
                    to={"/results?student=" + attempt.student}
                    className="recent-attempt"
                    key={attempt.id}
                  >
                    <span className="student-avatar">
                      {attempt.student_name.slice(0, 1)}
                    </span>
                    <div>
                      <strong>{attempt.student_name}</strong>
                      <p>{attempt.quiz_title}</p>
                    </div>
                    {attempt.status === "in_progress" ? (
                      <span className="badge in_progress">Jarayonda</span>
                    ) : (
                      <strong className="attempt-score">
                        {formatPercent(attempt.percentage)}%
                      </strong>
                    )}
                  </Link>
                ))
              ) : (
                <Empty text="Hali urinishlar yo‘q." />
              )}
            </section>
          </div>
        </>
      )}
      <ImportChooser open={importOpen} onClose={() => setImportOpen(false)} />
    </>
  );
}
