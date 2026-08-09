import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import apiFetch from "../api.ts";

const inputClass =
    "w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500";

function LoginPage() {
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError(null);

        try {
            const result = await apiFetch("/login", {
                method: "POST",
                body: JSON.stringify({ username, password }),
            });
            localStorage.setItem("token", result.token);
            navigate("/cars");
        } catch (err) {
            setError((err as Error).message);
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
            <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                <h1 className="text-xl font-semibold text-slate-900">Log in</h1>
                <p className="mt-1 text-sm text-slate-500">Servicd — car maintenance tracker</p>

                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" className={inputClass} />
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" className={inputClass} />
                    <button type="submit" className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">
                        Log In
                    </button>
                    {error && <p className="text-sm text-red-600">{error}</p>}
                </form>

                <p className="mt-6 text-center text-sm text-slate-500">
                    Don't have an account?{" "}
                    <Link to="/signup" className="font-medium text-slate-900 hover:underline">
                        Sign up
                    </Link>
                </p>
            </div>
        </div>
    );
}

export default LoginPage;
