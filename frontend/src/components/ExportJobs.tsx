import type { ExportJob, Page } from "../services/types";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { statusLabel } from "../services/labels";
import { Button } from "./ui/button";
import { Loading, ErrorState, Empty } from "./states";
export function ExportJobs() {
  const [page, setPage] = useState(1);
  const cache = useQueryClient();
  const q = useQuery({
    queryKey: ["export-jobs", page],
    queryFn: () => api<Page<ExportJob>>("reports/exports/?page=" + page),
    refetchInterval: (query) =>
      query.state.data?.results.some((j) => j.status === "pending")
        ? 2000
        : false,
  });
  useEffect(() => {
    const refresh = () => {
      cache.invalidateQueries({ queryKey: ["export-jobs"] });
    };
    window.addEventListener("export-started", refresh);
    return () => window.removeEventListener("export-started", refresh);
  }, [cache]);
  return (
    <section className="card padded" style={{ marginTop: 24 }}>
      <h2>Hisobotlar navbati</h2>
      <p className="hint">
        Katta hisobotlar fonda tayyorlanadi. Fayllar 7 kun saqlanadi.
      </p>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorState error={q.error} />
      ) : q.data.results.length ? (
        q.data.results.map((job) => (
          <div className="section-heading" key={job.id}>
            <div>
              <strong>
                {new Date(job.created_at).toLocaleString("uz-UZ", {
                  timeZone: "Asia/Tashkent",
                })}
              </strong>
              <p role="status">{statusLabel[job.status] || job.status}</p>
              {job.error && (
                <p role="alert" className="error">
                  {job.error}
                </p>
              )}
            </div>
            {job.status === "ready" && (
              <a
                className="button secondary-button"
                href={`/api/reports/exports/${job.id}/download/`}
                download
              >
                Yuklab olish
              </a>
            )}
          </div>
        ))
      ) : (
        <Empty text="Fonda tayyorlangan hisobotlar yo‘q." />
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
  );
}
