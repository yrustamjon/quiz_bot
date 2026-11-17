import { useUnsavedChanges } from "../components/useUnsavedChanges";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
const profileSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(3, "Ism va familiyangizni kiriting.")
    .max(150),
  email: z.union([z.email(), z.literal("")]),
  specialty: z.string().max(150),
});
import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../services/auth";
import { api } from "../services/api";
import { Button } from "../components/ui/button";
export default function Profile() {
  const { user, refresh } = useAuth();
  const form = useForm({
    resolver: zodResolver(profileSchema),
    values: {
      full_name: user?.full_name || "",
      email: user?.email || "",
      specialty: user?.specialty || "",
    },
  });
  useUnsavedChanges(form.formState.isDirty);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">HISOB SOZLAMALARI</div>
          <h1>Profil</h1>
          <p>Shaxsiy hisobingiz va xavfsizlik.</p>
        </div>
      </div>
      <section className="card padded">
        <h2>{user?.full_name || user?.username}</h2>
        <p className="hint">Login: {user?.username}</p>
        <form
          onSubmit={form.handleSubmit(async (values) => {
            setBusy(true);
            setError("");
            try {
              await api("profile/", {
                method: "PATCH",
                body: JSON.stringify(values),
              });
              await refresh();
              form.reset(values);
              setNotice("Profil saqlandi.");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          })}
        >
          <label>
            Ism va familiya
            <input
              {...form.register("full_name")}
              defaultValue={user?.full_name}
              required
              minLength={3}
              maxLength={150}
            />
          </label>
          <label>
            Email
            <input
              {...form.register("email")}
              defaultValue={user?.email}
              type="email"
            />
          </label>
          <label>
            Fan
            <input
              {...form.register("specialty")}
              defaultValue={user?.specialty}
              maxLength={150}
            />
          </label>
          {Object.keys(form.formState.errors).length > 0 && (
            <p role="alert" className="notice error">
              Ism yoki email maydonini tekshiring.
            </p>
          )}
          {error && (
            <p role="alert" className="notice error">
              {error}
            </p>
          )}
          {notice && <p role="status">{notice}</p>}
          <div className="actions">
            <Button disabled={busy}>Saqlash</Button>
            <Link className="button secondary-button" to="/change-password">
              Parolni almashtirish
            </Link>
          </div>
        </form>
      </section>
    </>
  );
}
