import { useEffect } from "react";
import { Toaster, toast } from "sonner";
export function Notifications() {
  useEffect(() => {
    const notify = (event: Event) => {
      const message = (event as CustomEvent<string>).detail;
      if (message) toast.success(message);
    };
    window.addEventListener("mutation-success", notify);
    return () => window.removeEventListener("mutation-success", notify);
  }, []);
  return (
    <Toaster
      position="bottom-right"
      closeButton
      toastOptions={{
        style: {
          background: "var(--surface)",
          color: "var(--text)",
          borderColor: "var(--border)",
        },
      }}
    />
  );
}
