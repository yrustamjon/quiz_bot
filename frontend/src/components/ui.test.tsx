import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Auth from "../pages/Auth";
import { ThemeToggle } from "./theme";
import { Modal } from "./ui/dialog";
import { Empty, ErrorState } from "./states";
vi.mock("../services/auth", () => ({
  useAuth: () => ({ user: undefined, refresh: vi.fn() }),
}));
describe("Accessible production components", () => {
  it("login validates required fields without sending credentials", async () => {
    render(
      <MemoryRouter>
        <Auth />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Hisobga kirish" }));
    await waitFor(() =>
      expect(screen.getByText("Loginni kiriting.")).toBeInTheDocument(),
    );
    expect(screen.getByText("Parolni kiriting.")).toBeInTheDocument();
    expect(screen.getByLabelText("Login yoki email")).toHaveAttribute(
      "autocomplete",
      "username",
    );
  });
  it("toggles and persists theme without storing credentials", () => {
    document.documentElement.classList.remove("dark");
    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole("button", { name: "Qorong‘i mavzu" }));
    expect(document.documentElement).toHaveClass("dark");
    expect(localStorage.theme).toBe("dark");
    fireEvent.click(screen.getByRole("button", { name: "Yorug‘ mavzu" }));
    expect(localStorage.theme).toBe("light");
  });
  it("dialog has a real accessible name and close control", () => {
    const close = vi.fn();
    render(
      <Modal open onOpenChange={close} title="Tasdiqlash">
        <p>Savollar saqlanadi.</p>
      </Modal>,
    );
    expect(
      screen.getByRole("dialog", { name: "Tasdiqlash" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yopish" }));
    expect(close).toHaveBeenCalledWith(false);
  });
  it("empty state describes real absence of records", () => {
    render(<Empty text="Test topilmadi." />);
    expect(
      screen.getByRole("heading", { name: "Test topilmadi." }),
    ).toBeInTheDocument();
  });
  it("error is announced and retry performs a real callback", () => {
    const retry = vi.fn();
    render(<ErrorState error={new Error("Tarmoq uzildi.")} retry={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Tarmoq uzildi.");
    fireEvent.click(screen.getByRole("button", { name: "Qayta urinish" }));
    expect(retry).toHaveBeenCalledOnce();
  });
});
