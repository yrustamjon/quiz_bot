import { NetworkStatus } from "../components/NetworkStatus";
import { AccountMenu } from "../components/AccountMenu";
import { useState } from "react";
import { NavLink, Outlet, Navigate, useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  GraduationCap,
  LayoutDashboard,
  BookOpen,
  Users,
  FileQuestion,
  Trophy,
  BarChart3,
  Settings,
  Menu,
  LogOut,
  PanelLeftClose,
} from "lucide-react";
import { useAuth } from "../services/auth";
import { post } from "../services/api";
import { ThemeToggle } from "../components/theme";
import { Modal } from "../components/ui/dialog";
import { Loading } from "../components/states";
export default function Shell() {
  const { user, loading, refresh } = useAuth();
  const query = useQueryClient();
  const [mobile, setMobile] = useState(false);
  const [error, setError] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  if (loading)
    return (
      <>
        <NetworkStatus />
        <Loading />
      </>
    );
  if (!user) return <Navigate to="/login" />;
  if (!["SUPER_ADMIN", "TEACHER"].includes(user.role))
    return (
      <p role="alert">Bu panel faqat o‘qituvchi va administrator uchun.</p>
    );
  if (user.must_change_password) return <Navigate to="/change-password" />;
  async function logout() {
    setLoggingOut(true);
    setError("");
    try {
      await post("auth/logout/");
      query.removeQueries({ predicate: (q) => q.queryKey[0] !== "me" });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoggingOut(false);
    }
  }
  const nav = [
    ["/", "Boshqaruv paneli", LayoutDashboard],
    ...(user.role === "SUPER_ADMIN"
      ? [["/teachers", "O‘qituvchilar", Users] as const]
      : []),
    [
      "/quizzes",
      user.role === "SUPER_ADMIN" ? "Testlar" : "Testlarim",
      BookOpen,
    ],
    ["/questions", "Savollar", FileQuestion],
    ["/students", "O‘quvchilar", Users],
    ...(user.role === "SUPER_ADMIN"
      ? [["/groups", "Guruhlar", Users] as const]
      : []),
    ["/results", "Natijalar", BarChart3],
    ["/rankings", "Reyting", Trophy],
    ["/reports", "Hisobotlar", BarChart3],
    ...(user.role === "SUPER_ADMIN"
      ? [["/settings", "Sozlamalar", Settings] as const]
      : [["/profile", "Profil", Settings] as const]),
  ] as const;
  const links = (
    <>
      {nav.map(([path, title, Icon]) => (
        <NavLink
          key={path as string}
          to={path as string}
          end={path === "/"}
          title={title as string}
          onClick={() => setMobile(false)}
        >
          <Icon size={20} />
          <span>{title as string}</span>
        </NavLink>
      ))}
    </>
  );
  return (
    <div className={"shell " + (collapsed ? "collapsed" : "")}>
      <a className="skip" href="#main">
        Asosiy tarkibga o‘tish
      </a>
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">
            <GraduationCap />
          </span>
          <span>Quiz Bot</span>
        </div>
        <div className="nav-label">BOSHQARUV</div>
        <nav>{links}</nav>
        <div className="sidebar-bottom">
          <div className="secure">
            <span className="dot" /> Himoyalangan muhit
          </div>
          <button
            className="icon"
            aria-label="Menyuni yig‘ish"
            onClick={() => setCollapsed(!collapsed)}
          >
            <PanelLeftClose />
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header>
          <button
            className="icon mobile-menu"
            aria-label="Menyuni ochish"
            onClick={() => setMobile(true)}
          >
            <Menu />
          </button>
          <span className="breadcrumb">
            Quiz Bot <span>/</span>{" "}
            {nav.find((x) => x[0] === location.pathname)?.[1] ||
              "Test tafsilotlari"}
          </span>
          <div className="header-actions">
            <ThemeToggle />
            <AccountMenu user={user} onLogout={logout} />
            <div className="user-caption">
              <strong>{user.full_name || user.username}</strong>
              <small>
                {user.role === "TEACHER" ? "O‘qituvchi" : "Administrator"}
              </small>
            </div>
            <button
              className="icon"
              aria-label="Hisobdan chiqish"
              onClick={logout}
              disabled={loggingOut}
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>
        <main id="main">
          <NetworkStatus />
          {error && (
            <p className="notice error" role="alert">
              {error}
            </p>
          )}
          <Outlet />
        </main>
        <footer>
          Quiz Bot <span>Vaqt mintaqasi: Toshkent (UTC+5)</span>
        </footer>
      </div>
      <Modal open={mobile} onOpenChange={setMobile} title="Navigatsiya">
        <nav className="mobile-nav">{links}</nav>
      </Modal>
    </div>
  );
}
