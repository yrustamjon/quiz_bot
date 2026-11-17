import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation } from "react-router-dom";
import { ConfirmDialog } from "./ConfirmDialog";
const Context = createContext<(message: string) => Promise<boolean>>(
  async () => false,
);
export function ConfirmationProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState("");
  const resolve = useRef<((value: boolean) => void) | undefined>(undefined);
  const location = useLocation();
  const finish = useCallback((value: boolean) => {
    resolve.current?.(value);
    resolve.current = undefined;
    setMessage("");
  }, []);
  const ask = useCallback((text: string) => {
    if (resolve.current) return Promise.resolve(false);
    setMessage(text);
    return new Promise<boolean>((done) => {
      resolve.current = done;
    });
  }, []);
  useEffect(() => {
    finish(false);
  }, [location.pathname, finish]);
  useEffect(
    () => () => {
      resolve.current?.(false);
    },
    [],
  );
  return (
    <Context.Provider value={ask}>
      {children}
      <ConfirmDialog
        open={!!message}
        title="Amalni tasdiqlash"
        description={message}
        onCancel={() => finish(false)}
        onConfirm={() => finish(true)}
      />
    </Context.Provider>
  );
}
export const useConfirmation = () => useContext(Context);
