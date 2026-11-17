import type { Question, Page } from "../services/types";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { Button } from "./ui/button";
import { Loading, Empty, ErrorState } from "./states";
export function QuestionBank({
  quizId,
  ownerId,
  selected,
  onSaved,
}: {
  quizId: string;
  ownerId: number;
  selected: { id: number; text: string }[];
  onSaved: () => void;
}) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const bank = useQuery({
    queryKey: ["question-bank", search, page],
    queryFn: () =>
      api<Page<Question>>(
        `questions/?search=${encodeURIComponent(search)}&page=${page}`,
      ),
  });
  async function save(ids: number[]) {
    setBusy(true);
    setError("");
    try {
      await api(`quizzes/${quizId}/questions/`, {
        method: "PUT",
        body: JSON.stringify({ question_ids: ids }),
      });
      onSaved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <h3 style={{ marginTop: 24 }}>Tanlangan savollar</h3>
      {selected.map((q, i) => (
        <div key={q.id} className="notice">
          <span style={{ flex: 1 }}>
            {i + 1}. {q.text}
          </span>
          <div className="actions">
            <Button
              variant="outline"
              disabled={busy || i === 0}
              aria-label={`${i + 1}-savolni yuqoriga`}
              onClick={() => {
                const ids = selected.map((x) => x.id);
                [ids[i - 1], ids[i]] = [ids[i], ids[i - 1]];
                save(ids);
              }}
            >
              ↑
            </Button>
            <Button
              variant="outline"
              disabled={busy || i === selected.length - 1}
              aria-label={`${i + 1}-savolni pastga`}
              onClick={() => {
                const ids = selected.map((x) => x.id);
                [ids[i + 1], ids[i]] = [ids[i], ids[i + 1]];
                save(ids);
              }}
            >
              ↓
            </Button>
            <Button
              variant="outline"
              disabled={busy}
              onClick={() =>
                save(selected.filter((x) => x.id !== q.id).map((x) => x.id))
              }
            >
              Ajratish
            </Button>
          </div>
        </div>
      ))}
      <h3>Savollar bankidan tanlash</h3>
      <label>
        Bankdan qidirish
        <input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </label>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {bank.isPending ? (
        <Loading />
      ) : bank.error ? (
        <ErrorState error={bank.error} retry={() => bank.refetch()} />
      ) : (
        bank.data.results
          .filter(
            (q) => q.owner === ownerId && !selected.some((s) => s.id === q.id),
          )
          .map((q) => (
            <div className="section-heading" key={q.id}>
              <p>{q.text}</p>
              <Button
                variant="outline"
                disabled={busy}
                onClick={() => save([...selected.map((x) => x.id), q.id])}
              >
                Tanlash
              </Button>
            </div>
          ))
      )}
      {bank.data?.count === 0 && <Empty />}
      <div className="pagination">
        <span>{page}-sahifa</span>
        <Button
          variant="outline"
          disabled={!bank.data?.previous}
          onClick={() => setPage(page - 1)}
        >
          Oldingi
        </Button>
        <Button
          variant="outline"
          disabled={!bank.data?.next}
          onClick={() => setPage(page + 1)}
        >
          Keyingi
        </Button>
      </div>
    </>
  );
}
