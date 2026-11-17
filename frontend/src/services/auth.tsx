import { createContext, useContext, useEffect, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type User } from "./api";
const Context = createContext<{
  user?: User;
  loading: boolean;
  refresh: () => Promise<void>;
}>({ loading: true, refresh: async () => {} });
export function AuthProvider({ children }: { children: ReactNode }) {
  const cache = useQueryClient();
  const q = useQuery({
    queryKey: ["me"],
    queryFn: () => api<User>("auth/me/"),
    retry: false,
  });
  useEffect(() => {
    const check = async () => {
      const result = await q.refetch();
      if (result.isError)
        cache.removeQueries({ predicate: (item) => item.queryKey[0] !== "me" });
    };
    window.addEventListener("auth-check-required", check);
    return () => window.removeEventListener("auth-check-required", check);
  }, [cache, q.refetch]);
  return (
    <Context.Provider
      value={{
        user: q.isError ? undefined : q.data,
        loading: q.isPending,
        refresh: async () => {
          await q.refetch();
        },
      }}
    >
      {children}
    </Context.Provider>
  );
}
export const useAuth = () => useContext(Context);
