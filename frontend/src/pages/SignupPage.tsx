import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import apiFetch from "../api.ts";


function SignupPage() {
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError(null);
        
        try {
            await apiFetch("/users", {
                method: "POST",
                body: JSON.stringify({ username, name, password }),
            });
            navigate("/login");
        } catch (err) {
            setError((err as Error).message);
            }
        }
    
    return (
        <form onSubmit={handleSubmit}>
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" />
            <button type="submit">Sign Up</button>
            {error && <p>{error}</p>}
        </form>
    );

}

export default SignupPage;