import { useState } from "react";
import { NavLink, Link, Outlet, Navigate, useLocation } from "react-router-dom";
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
  ChevronRight,
  type LucideIcon,
} from "lucide-react";
import { NetworkStatus } from "../components/NetworkStatus";
import { AccountMenu } from "../components/AccountMenu";
import { ThemeToggle } from "../components/theme";
import { Modal } from "../components/ui/dialog";
import { Loading } from "../components/states";
import { useAuth } from "../services/auth";
import { post } from "../services/api";
type NavItem = { path: string; title: string; Icon: LucideIcon };
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
  const admin = user.role === "SUPER_ADMIN";
  const sections: { label: string; items: NavItem[] }[] = [
    {
      label: "ISH MAYDONI",
      items: [
        { path: "/", title: "Boshqaruv paneli", Icon: LayoutDashboard },
        {
          path: "/quizzes",
          title: admin ? "Testlar" : "Testlarim",
          Icon: BookOpen,
        },
        { path: "/questions", title: "Savollar", Icon: FileQuestion },
      ],
    },
    {
      label: "TAHLIL VA NATIJALAR",
      items: [
        { path: "/students", title: "O‘quvchilar", Icon: Users },
        { path: "/results", title: "Natijalar", Icon: BarChart3 },
        { path: "/rankings", title: "Reyting", Icon: Trophy },
        { path: "/reports", title: "Hisobotlar", Icon: BarChart3 },
      ],
    },
    {
      label: "BOSHQARUV",
      items: admin
        ? [
            { path: "/teachers", title: "O‘qituvchilar", Icon: Users },
            { path: "/groups", title: "Guruhlar", Icon: Users },
            { path: "/settings", title: "Sozlamalar", Icon: Settings },
          ]
        : [{ path: "/profile", title: "Profil", Icon: Settings }],
    },
  ];
  const current =
    sections
      .flatMap((s) => s.items)
      .find((item) => item.path === location.pathname)?.title ||
    (location.pathname === "/profile"
      ? "Profil"
      : location.pathname.startsWith("/students/")
        ? "O‘quvchi profili"
        : "Test tafsilotlari");
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
  const links = (
    <>
      {sections.map((section) => (
        <div className="nav-section" key={section.label}>
          <div className="nav-label">{section.label}</div>
          <div className="nav-links">
            {section.items.map(({ path, title, Icon }) => (
              <NavLink
                key={path}
                to={path}
                end={path === "/"}
                title={title}
                onClick={() => setMobile(false)}
              >
                <Icon size={19} strokeWidth={1.7} />
                <span>{title}</span>
              </NavLink>
            ))}
          </div>
        </div>
      ))}
    </>
  );
  return (
    <div className={"shell " + (collapsed ? "collapsed" : "")}>
      <a className="skip" href="#main">
        Asosiy tarkibga o‘tish
      </a>
      <aside className="sidebar">
        <Link to="/" className="brand" aria-label="Boshqaruv paneliga o‘tish">
          <span className="brand-icon">
            <GraduationCap size={24} />
          </span>
          <span className="brand-copy">
            <strong>
              Quiz Bot<span className="brand-period">.</span>
            </strong>
            <small>Bilimni baholash platformasi</small>
          </span>
        </Link>
        <nav aria-label="Asosiy menyu">{links}</nav>
        <div className="sidebar-bottom">
          <div className="workspace-label">
            <span className="workspace-indicator" />
            <div>
              <strong>{admin ? "Administrator" : "O‘qituvchi"}</strong>
              <small>Shaxsiy ish maydoni</small>
            </div>
          </div>
          <button
            className="icon"
            aria-label={collapsed ? "Menyuni kengaytirish" : "Menyuni yig‘ish"}
            aria-expanded={!collapsed}
            title={collapsed ? "Menyuni kengaytirish" : "Menyuni yig‘ish"}
            onClick={() => setCollapsed(!collapsed)}
          >
            <PanelLeftClose size={18} />
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header>
          <div className="header-location">
            <button
              className="icon mobile-menu"
              aria-label="Menyuni ochish"
              onClick={() => setMobile(true)}
            >
              <Menu size={21} />
            </button>
            <span className="breadcrumb">
              <span className="breadcrumb-root">Ish maydoni</span>
              <ChevronRight size={14} />
              <strong>{current}</strong>
            </span>
          </div>
          <div className="header-actions">
            <ThemeToggle />
            <span className="header-divider" />
            <AccountMenu user={user} onLogout={logout} />
            <button
              className="icon logout-button"
              aria-label="Hisobdan chiqish"
              title="Hisobdan chiqish"
              onClick={logout}
              disabled={loggingOut}
            >
              <LogOut size={17} />
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
          <span>
            Quiz Bot <span className="footer-dot">·</span> Ta’lim uchun
            yaratilgan
          </span>
          <span>Toshkent · UTC+5</span>
        </footer>
      </div>
      <Modal
        open={mobile}
        onOpenChange={setMobile}
        title="Navigatsiya"
        description="Ish maydoni va natijalar bo‘limini tanlang."
      >
        <nav className="mobile-nav" aria-label="Mobil menyu">
          {links}
        </nav>
      </Modal>
    </div>
  );
}
