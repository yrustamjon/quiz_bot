import { Modal } from "./ui/dialog";
import { Button } from "./ui/button";
export function ConfirmDialog({
  open,
  onCancel,
  onConfirm,
  title,
  description,
  busy = false,
}: {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  busy?: boolean;
}) {
  return (
    <Modal
      open={open}
      onOpenChange={(v) => {
        if (!v && !busy) onCancel();
      }}
      title={title}
      description={description}
    >
      <div className="actions">
        <Button variant="outline" disabled={busy} onClick={onCancel}>
          Bekor qilish
        </Button>
        <Button variant="destructive" disabled={busy} onClick={onConfirm}>
          {busy ? "Bajarilmoqda…" : "Tasdiqlash"}
        </Button>
      </div>
    </Modal>
  );
}
