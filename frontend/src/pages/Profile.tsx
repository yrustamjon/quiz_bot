import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../services/auth";
import { api } from "../services/api";
import { Button } from "../components/ui/button";
export default function Profile() {
  const { user, refresh } = useAuth();
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
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            const d = new FormData(e.currentTarget);
            try {
              await api("profile/", {
                method: "PATCH",
                body: JSON.stringify(Object.fromEntries(d)),
              });
              await refresh();
              setNotice("Profil saqlandi.");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Ism va familiya
            <input
              name="full_name"
              defaultValue={user?.full_name}
              required
              minLength={3}
              maxLength={150}
            />
          </label>
          <label>
            Email
            <input name="email" defaultValue={user?.email} type="email" />
          </label>
          <label>
            Fan
            <input
              name="specialty"
              defaultValue={user?.specialty}
              maxLength={150}
            />
          </label>
          {error && (
            <p role="alert" className="notice error">
              {error}
            </p>
          )}
          {notice && <p role="status">{notice}</p>}
          <div className="actions">
            <Button disabled={busy}>Saqlash</Button>
            <Link className="button outline" to="/change-password">
              Parolni almashtirish
            </Link>
          </div>
        </form>
      </section>
    </>
  );
}
