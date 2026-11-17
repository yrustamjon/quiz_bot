import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Shell from "../layouts/Shell";
const auth = vi.hoisted(() => vi.fn());
vi.mock("../services/auth", () => ({ useAuth: auth }));
function renderShell(user: unknown) {
  auth.mockReturnValue({ user, loading: false, refresh: vi.fn() });
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/login" element={<p>Hisobga kirish sahifasi</p>} />
          <Route
            path="/change-password"
            element={<p>Majburiy yangi parol</p>}
          />
          <Route element={<Shell />}>
            <Route index element={<h1>Himoyalangan tarkib</h1>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
describe("Frontend routing boundaries", () => {
  it("anonymous identity redirects before rendering private content", () => {
    renderShell(undefined);
    expect(screen.getByText("Hisobga kirish sahifasi")).toBeInTheDocument();
    expect(screen.queryByText("Himoyalangan tarkib")).not.toBeInTheDocument();
  });
  it("temporary password forces replacement", () => {
    renderShell({ role: "TEACHER", must_change_password: true });
    expect(screen.getByText("Majburiy yangi parol")).toBeInTheDocument();
  });
  it("student cannot render administrator shell", () => {
    renderShell({ role: "STUDENT" });
    expect(screen.getByRole("alert")).toHaveTextContent("faqat o‘qituvchi");
    expect(screen.queryByText("Himoyalangan tarkib")).not.toBeInTheDocument();
  });
  it("teacher sees permitted routes and no global management links", () => {
    renderShell({
      role: "TEACHER",
      username: "teacher",
      full_name: "Test Teacher",
      must_change_password: false,
    });
    expect(
      screen.getByRole("heading", { name: "Himoyalangan tarkib" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "O‘qituvchilar" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Guruhlar" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Testlarim" })).toBeInTheDocument();
  });
});
