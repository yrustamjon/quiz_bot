import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, type Quiz } from "../services/api";
import type { Page } from "../services/types";
import { Modal } from "./ui/dialog";
import { Button } from "./ui/button";
import { Loading, ErrorState, Empty } from "./states";
export function ImportChooser({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [page, setPage] = useState(1);
  const [target, setTarget] = useState("");
  const navigate = useNavigate();
  const q = useQuery({
    queryKey: ["import-quiz-choices", page],
    queryFn: () => api<Page<Quiz>>("quizzes/?status=draft&page=" + page),
    enabled: open,
  });
  return (
    <Modal
      open={open}
      onOpenChange={(v) => {
        if (!v) onClose();
      }}
      title="Excel importi"
      description="Savollar qo‘shiladigan qoralamani tanlang."
    >
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorState error={q.error} />
      ) : q.data?.results.length ? (
        <>
          <label>
            Import uchun test
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">Testni tanlang</option>
              {q.data.results.map((quiz) => (
                <option key={quiz.id} value={quiz.id}>
                  {quiz.title}
                </option>
              ))}
            </select>
          </label>
          <div className="pagination">
            <Button
              variant="outline"
              disabled={!q.data.previous}
              onClick={() => setPage(page - 1)}
            >
              Oldingi
            </Button>
            <Button
              variant="outline"
              disabled={!q.data.next}
              onClick={() => setPage(page + 1)}
            >
              Keyingi
            </Button>
          </div>
          <Button
            disabled={!target}
            onClick={() => {
              onClose();
              navigate(`/quizzes/${target}?import=1`);
            }}
          >
            Importni ochish
          </Button>
        </>
      ) : (
        <>
          <Empty text="Avval test qoralamasini yarating." />
          <Link
            className="button primary"
            to="/quizzes?create=1"
            onClick={onClose}
          >
            Test yaratish
          </Link>
        </>
      )}
    </Modal>
  );
}
