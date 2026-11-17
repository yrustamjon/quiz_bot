import { useId, useRef, useState, type ChangeEventHandler } from "react";
import { Upload } from "lucide-react";
import { Button } from "./ui/button";
export function FileUpload({
  label,
  accept,
  disabled = false,
  onChange,
}: {
  label: string;
  accept: string;
  disabled?: boolean;
  onChange: ChangeEventHandler<HTMLInputElement>;
}) {
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  return (
    <div
      className="file-upload"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        if (disabled) return;
        if (e.dataTransfer.files.length !== 1) {
          setError("Bitta fayl tanlang.");
          return;
        }
        if (input.current) {
          input.current.files = e.dataTransfer.files;
          input.current.dispatchEvent(new Event("change", { bubbles: true }));
        }
      }}
    >
      <label htmlFor={id}>{label}</label>
      <input
        className="sr-only"
        ref={input}
        id={id}
        tabIndex={-1}
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={(e) => {
          setError("");
          setName(e.target.files?.[0]?.name || "");
          onChange(e);
        }}
      />
      <Button
        type="button"
        variant="outline"
        disabled={disabled}
        onClick={() => input.current?.click()}
      >
        <Upload size={17} />
        Fayl tanlash
      </Button>
      <p className="hint">
        {name || "Faylni shu joyga tashlang yoki tanlang."}
      </p>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </div>
  );
}
