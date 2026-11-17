import { StrictMode, useState } from "react";
import {
  act,
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import {
  createMemoryRouter,
  RouterProvider,
  Outlet,
  Link,
} from "react-router-dom";
import { it, expect } from "vitest";
import { ConfirmationProvider } from "./ConfirmationProvider";
import { UnsavedChangesProvider, useUnsavedChanges } from "./useUnsavedChanges";
function Form() {
  const [dirty, setDirty] = useState(false);
  useUnsavedChanges(dirty);
  return (
    <>
      <h1>Forma</h1>
      <input aria-label="Tahrir" onChange={() => setDirty(true)} />
      <Link to="/other">Chiqish</Link>
    </>
  );
}
function setup() {
  const router = createMemoryRouter(
    [
      {
        element: (
          <ConfirmationProvider>
            <UnsavedChangesProvider>
              <Outlet />
            </UnsavedChangesProvider>
          </ConfirmationProvider>
        ),
        children: [
          { path: "/form", element: <Form /> },
          { path: "/other", element: <h1>Boshqa sahifa</h1> },
        ],
      },
    ],
    { initialEntries: ["/other", "/form"] },
  );
  render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>,
  );
  return router;
}
it("protects dirty forms on Back and links, preserves edits on cancel, then proceeds on confirmation", async () => {
  const router = setup();
  fireEvent.change(screen.getByLabelText("Tahrir"), {
    target: { value: "Saqlanmagan" },
  });
  await act(async () => {
    await router.navigate(-1);
  });
  await screen.findByRole("dialog", { name: "Amalni tasdiqlash" });
  fireEvent.click(screen.getByRole("button", { name: "Bekor qilish" }));
  await waitFor(() =>
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
  );
  expect(screen.getByLabelText("Tahrir")).toHaveValue("Saqlanmagan");
  fireEvent.click(screen.getByRole("link", { name: "Chiqish" }));
  await screen.findByRole("dialog", { name: "Amalni tasdiqlash" });
  fireEvent.click(screen.getByRole("button", { name: "Tasdiqlash" }));
  await screen.findByRole("heading", { name: "Boshqa sahifa" });
});
it("allows navigation when there are no unsaved changes", async () => {
  setup();
  fireEvent.click(screen.getByRole("link", { name: "Chiqish" }));
  await screen.findByRole("heading", { name: "Boshqa sahifa" });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
