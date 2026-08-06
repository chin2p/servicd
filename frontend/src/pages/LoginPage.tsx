import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import apiFetch from "../api.ts";


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
        <form onSubmit={handleSubmit}>
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
            <button type="submit">Log In</button>
            {error && <p>{error}</p>}
        </form>
    );
}

export default LoginPage;