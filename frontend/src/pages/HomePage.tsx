import { Navigate, Link } from "react-router-dom";

function HomePage() {
    const token = localStorage.getItem("token");

    if (token) {
        return <Navigate to="/cars" replace />;
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
            <div className="max-w-md text-center">
                <h1 className="text-3xl font-semibold text-slate-900">Servicd</h1>
                <p className="mt-3 text-slate-600">
                    Track every service, part, and mile on your cars — and know what's coming
                    up next before it does.
                </p>
                <div className="mt-8 flex justify-center gap-3">
                    <Link
                        to="/signup"
                        className="rounded-md bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
                    >
                        Sign Up
                    </Link>
                    <Link
                        to="/login"
                        className="rounded-md border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-900 hover:bg-slate-100"
                    >
                        Log In
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default HomePage;
