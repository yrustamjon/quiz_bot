import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, Navigate } from "react-router-dom";
import {
  Eye,
  EyeOff,
  GraduationCap,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";
import { post } from "../services/api";
import { useAuth } from "../services/auth";
import { Button } from "../components/ui/button";
import { ThemeToggle } from "../components/theme";
const schema = z.object({
  username: z.string().min(1, "Loginni kiriting."),
  password: z.string().min(1, "Parolni kiriting."),
});
export default function Auth({ change = false }: { change?: boolean }) {
  const { user, refresh, loading } = useAuth();
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const formSchema = schema
    .extend({ new_password: z.string(), confirm_password: z.string() })
    .superRefine((data, ctx) => {
      if (change) {
        if (data.new_password.length < 8)
          ctx.addIssue({
            code: "custom",
            path: ["new_password"],
            message: "Kamida 8 belgili parol kiriting.",
          });
        if (data.new_password !== data.confirm_password)
          ctx.addIssue({
            code: "custom",
            path: ["confirm_password"],
            message: "Parollar mos emas.",
          });
      }
    });
  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: change ? "password-change" : "",
      password: "",
      new_password: "",
      confirm_password: "",
    },
  });
  if (change && !loading && !user) return <Navigate to="/login" />;
  if (!change && user)
    return (
      <Navigate to={user.must_change_password ? "/change-password" : "/"} />
    );
  if (done) return <Navigate to="/" />;
  return (
    <div className="auth">
      <div className="auth-top">
        <Link to="/login" className="brand">
          <span className="brand-icon">
            <GraduationCap />
          </span>
          Quiz Bot<span className="tag">TA’LIM PLATFORMASI</span>
        </Link>
        <ThemeToggle />
      </div>
      <main className="auth-content">
        <section className="auth-story">
          <div className="eyebrow">
            <span className="dot" /> BILIMNI ANIQLIK BILAN BAHOLANG
          </div>
          <h1>
            Yaxshi ta’lim.
            <br />
            <span>Aniq natijalar.</span>
          </h1>
          <p>
            Test yaratishdan natijalarni tahlil qilishgacha — o‘qituvchi uchun
            zarur vositalar bir joyda.
          </p>
          <div className="story-item">
            <ShieldCheck />
            <div>
              <strong>Ishonchli baholash</strong>
              <p>Saqlanadigan javoblar va server nazoratidagi vaqt.</p>
            </div>
          </div>
          <div className="story-foot">
            O‘rgatishga ko‘proq vaqt. Boshqarishga kamroq.
          </div>
        </section>
        <section className="auth-card">
          <span className="eyebrow">QUIZ BOT HISOBI</span>
          <h2>{change ? "Parolni almashtirish" : "Xush kelibsiz"}</h2>
          <p>
            {change
              ? "Xavfsizlik uchun yangi shaxsiy parol o‘rnating."
              : "Ishni davom ettirish uchun hisobingizga kiring."}
          </p>
          <form
            onSubmit={form.handleSubmit(async (v) => {
              setError("");
              try {
                if (change) {
                  await post("auth/change-password/", {
                    old_password: v.password,
                    new_password: v.new_password,
                    confirm_password: v.confirm_password,
                  });
                } else await post("auth/login/", v);
                await refresh();
                setDone(true);
              } catch (e) {
                setError((e as Error).message);
              }
            })}
            noValidate
          >
            {!change && (
              <label>
                Login yoki email
                <input
                  aria-label="Login yoki email"
                  autoComplete="username"
                  placeholder="Loginni kiriting"
                  {...form.register("username")}
                />
                <small role="alert">
                  {form.formState.errors.username?.message}
                </small>
              </label>
            )}
            <label>
              {change ? "Amaldagi parol" : "Parol"}
              <div className="password">
                <input
                  type={visible ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Parolingizni kiriting"
                  {...form.register("password")}
                />
                <button
                  type="button"
                  className="icon"
                  aria-label="Parolni ko‘rsatish"
                  onClick={() => setVisible(!visible)}
                >
                  {visible ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <small role="alert">
                {form.formState.errors.password?.message}
              </small>
            </label>
            {change && (
              <>
                <label>
                  Yangi parol
                  <input
                    {...form.register("new_password")}
                    aria-label="Yangi parol"
                    type="password"
                    autoComplete="new-password"
                    minLength={8}
                    required
                  />
                  <small role="alert">
                    {form.formState.errors.new_password?.message}
                  </small>
                </label>
                <label>
                  Yangi parolni tasdiqlang
                  <input
                    {...form.register("confirm_password")}
                    aria-label="Yangi parolni tasdiqlang"
                    type="password"
                    autoComplete="new-password"
                    required
                  />
                  <small role="alert">
                    {form.formState.errors.confirm_password?.message}
                  </small>
                </label>
                <p className="hint">
                  Kamida 8 belgi. Oddiy yoki faqat raqamlardan iborat parol
                  ishlatmang.
                </p>
              </>
            )}
            {error && (
              <div role="alert" className="notice error">
                {error}
              </div>
            )}
            <Button className="full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting
                ? "Kutilmoqda…"
                : change
                  ? "Parolni saqlash"
                  : "Hisobga kirish"}
              <ArrowRight size={17} />
            </Button>
          </form>
          <div className="auth-help">
            Hisobingiz yo‘qmi?
            <br />
            <strong>Administrator bilan bog‘laning.</strong>
          </div>
        </section>
      </main>
      <footer>
        © {new Date().getFullYear()} Quiz Bot. Bilimga yo‘l ochamiz.
        <span>Himoyalangan sessiya · Maxfiy ma’lumotlar saqlanadi</span>
      </footer>
    </div>
  );
}
