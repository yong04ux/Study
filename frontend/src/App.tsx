import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "./contexts/auth-context";

const navItems = [
  { to: "/dashboard", label: "\u6211\u7684\u5de5\u4f5c\u53f0" },
  { to: "/recommendation", label: "\u5fd7\u613f\u63a8\u8350" },
  { to: "/plans", label: "\u6211\u7684\u65b9\u6848" },
  { to: "/schools", label: "\u9662\u6821\u67e5\u8be2" },
  { to: "/qa", label: "\u667a\u80fd\u95ee\u7b54" },
  { to: "/reports", label: "\u62a5\u544a\u67e5\u8be2" },
];

export default function App() {
  const { currentUser, isAuthenticated, loadingUser, logout } = useAuth();

  return (
    <div className="min-h-screen text-ink">
      <div className="absolute inset-x-0 top-0 -z-10 h-[34rem] bg-[linear-gradient(180deg,rgba(8,47,73,0.03)_0%,rgba(236,253,245,0.08)_100%)]" />
      <div className="absolute inset-0 -z-10 bg-grid-fade bg-[size:40px_40px] [mask-image:linear-gradient(to_bottom,white,transparent_82%)]" />

      <div className="page-shell relative min-h-screen">
        <header className="sticky top-3 z-20 rounded-xl border border-white/80 bg-[rgba(255,255,255,0.84)] px-4 py-4 shadow-soft backdrop-blur sm:px-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <NavLink to="/" className="flex items-center gap-3 text-slate-900">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#0f172a_0%,#0369a1_100%)] text-sm font-bold text-white shadow-lg shadow-sky-900/20">
                GP
              </span>
              <span>
                <span className="block text-lg font-semibold">GaokaoPilot</span>
                <span className="block text-xs uppercase tracking-[0.16em] text-sky-700">
                  Education Intelligence Demo
                </span>
              </span>
            </NavLink>

            <nav className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    [
                      "rounded-lg px-4 py-2.5 text-center text-sm font-medium transition",
                      isActive
                        ? "bg-slate-950 text-white shadow-lg shadow-slate-900/15"
                        : "bg-slate-100/90 text-slate-700 hover:bg-slate-200",
                    ].join(" ")
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>

            <div className="flex flex-wrap items-center gap-2">
              {isAuthenticated && currentUser ? (
                <>
                  <div className="rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                    {currentUser.username}
                  </div>
                  <button
                    type="button"
                    onClick={logout}
                    className="inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
                  >
                    {"\u9000\u51fa\u767b\u5f55"}
                  </button>
                </>
              ) : loadingUser ? (
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
                  {"\u6b63\u5728\u52a0\u8f7d\u8d26\u53f7..."}
                </div>
              ) : (
                <>
                  <NavLink
                    to="/login"
                    className="inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
                  >
                    {"\u767b\u5f55"}
                  </NavLink>
                  <NavLink
                    to="/register"
                    className="inline-flex min-h-11 items-center justify-center rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(15,23,42,0.18)] transition hover:bg-slate-800"
                  >
                    {"\u6ce8\u518c"}
                  </NavLink>
                </>
              )}
            </div>
          </div>
        </header>

        <main className="relative flex-1 pb-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
