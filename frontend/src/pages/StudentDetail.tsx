import { formatPercent } from "../services/labels";
import type { Student } from "../services/types";
import { statusLabel } from "../services/labels";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { Loading, ErrorState, Empty } from "../components/states";
export default function StudentDetail() {
  const { id } = useParams();
  const q = useQuery({
    queryKey: ["student", id],
    queryFn: () => api<Student>("students/" + id + "/"),
  });
  if (q.isPending) return <Loading />;
  if (q.error) return <ErrorState error={q.error} retry={() => q.refetch()} />;
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{q.data.full_name}</h1>
          <p>Faqat ruxsat berilgan testlardagi ishtirok.</p>
        </div>
        <Link className="button secondary-button" to={"/results?student=" + id}>
          Barcha natijalar
        </Link>
      </div>
      <div className="stat-grid">
        <section className="card stat">
          <p>Urinishlar</p>
          <strong>{q.data.participation_count}</strong>
        </section>
        <section className="card stat">
          <p>O‘rtacha natija</p>
          <strong>{q.data.average_percentage ?? "—"}%</strong>
        </section>
      </div>
      <section className="card padded">
        <h2>So‘nggi 25 urinish</h2>
        {q.data.attempts?.length ? (
          q.data.attempts.map((a) => (
            <div className="section-heading" key={a.id}>
              <Link to={"/quizzes/" + a.quiz}>{a.quiz_title}</Link>
              <span>
                {formatPercent(a.percentage)}% ·{" "}
                {statusLabel[a.status] || a.status}
              </span>
            </div>
          ))
        ) : (
          <Empty />
        )}
      </section>
    </>
  );
}
