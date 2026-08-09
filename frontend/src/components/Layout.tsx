import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";

function Layout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <Link to="/cars" className="text-lg font-semibold text-slate-900">
            Servicd
          </Link>
          <button
            onClick={handleLogout}
            className="text-sm font-medium text-slate-500 hover:text-slate-900"
          >
            Log out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-10">{children}</main>
    </div>
  );
}

export default Layout;
