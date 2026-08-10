import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import apiFetch from "../api";

function Layout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  async function handleDeleteAccount() {
    if (
      !window.confirm(
        "Delete your account? This will permanently delete all your cars and service history."
      )
    ) {
      return;
    }
    try {
      await apiFetch("/users/me", { method: "DELETE" });
      localStorage.removeItem("token");
      navigate("/login");
    } catch (err) {
      alert((err as Error).message);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <Link to="/cars" className="text-lg font-semibold text-slate-900">
            Servicd
          </Link>
          <div className="flex items-center gap-4">
            <button
              onClick={handleDeleteAccount}
              className="text-sm font-medium text-red-600 hover:text-red-800"
            >
              Delete Account
            </button>
            <button
              onClick={handleLogout}
              className="text-sm font-medium text-slate-500 hover:text-slate-900"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-10">{children}</main>
    </div>
  );
}

export default Layout;
