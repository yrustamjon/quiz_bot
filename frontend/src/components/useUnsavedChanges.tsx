import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import { useBlocker } from "react-router-dom";
import { useConfirmation } from "./ConfirmationProvider";
type Register = (id: symbol) => () => void;
const Context = createContext<Register | undefined>(undefined);
export function UnsavedChangesProvider({ children }: { children: ReactNode }) {
  const dirty = useRef(new Set<symbol>());
  const asking = useRef(false);
  const confirmAction = useConfirmation();
  const register = useCallback((id: symbol) => {
    dirty.current.add(id);
    return () => {
      dirty.current.delete(id);
    };
  }, []);
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      currentLocation.pathname !== nextLocation.pathname &&
      dirty.current.size > 0,
  );
  useEffect(() => {
    if (blocker.state !== "blocked" || asking.current) return;
    asking.current = true;
    void confirmAction(
      "Saqlanmagan o‘zgarishlar bor. Sahifadan chiqasizmi?",
    ).then((leave) => {
      asking.current = false;
      if (leave) blocker.proceed();
      else blocker.reset();
    });
  }, [blocker, confirmAction]);
  return <Context.Provider value={register}>{children}</Context.Provider>;
}
export function useUnsavedChanges(dirty: boolean) {
  const register = useContext(Context);
  const id = useRef(Symbol("unsaved-form"));
  const unregister = useRef<(() => void) | undefined>(undefined);
  useEffect(() => {
    if (!dirty) return;
    unregister.current = register?.(id.current);
    return () => {
      unregister.current?.();
      unregister.current = undefined;
    };
  }, [dirty, register]);
  useEffect(() => {
    if (!dirty) return;
    const unload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", unload);
    return () => window.removeEventListener("beforeunload", unload);
  }, [dirty]);
  return useCallback(() => {
    unregister.current?.();
    unregister.current = undefined;
  }, []);
}
