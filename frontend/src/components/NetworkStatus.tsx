import { useSyncExternalStore } from "react";
import { WifiOff } from "lucide-react";
function subscribe(notify: () => void) {
  window.addEventListener("online", notify);
  window.addEventListener("offline", notify);
  return () => {
    window.removeEventListener("online", notify);
    window.removeEventListener("offline", notify);
  };
}
export function NetworkStatus() {
  const online = useSyncExternalStore(
    subscribe,
    () => navigator.onLine,
    () => true,
  );
  if (online) return null;
  return (
    <div className="notice error" role="alert">
      <WifiOff aria-hidden="true" />
      <div>
        <strong>Internet aloqasi uzildi.</strong>
        <p>
          Qayta ulanganda ma’lumotlar avtomatik yangilanadi. Saqlanmagan
          tahrirlaringiz shu sahifada qoladi.
        </p>
      </div>
    </div>
  );
}
