import { AlertCircle, Inbox } from "lucide-react";
export function Loading() {
  return (
    <div role="status" aria-label="Yuklanmoqda" className="skeleton-grid">
      {[1, 2, 3].map((x) => (
        <div key={x} className="skeleton" />
      ))}
    </div>
  );
}
export function ErrorState({
  error,
  retry,
}: {
  error: Error;
  retry?: () => void;
}) {
  return (
    <div role="alert" className="notice error">
      <AlertCircle />
      <div>
        <strong>Ma’lumotni yuklab bo‘lmadi</strong>
        <p>{error.message}</p>
        {retry && <button onClick={retry}>Qayta urinish</button>}
      </div>
    </div>
  );
}
export function Empty({
  text = "Hozircha ma’lumot mavjud emas.",
}: {
  text?: string;
}) {
  return (
    <div className="empty">
      <Inbox size={34} />
      <h3>{text}</h3>
      <p>Ma’lumot qo‘shilgach shu yerda ko‘rinadi.</p>
    </div>
  );
}
