const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default async function apiFetch(path: string, options: RequestInit = {}) {
    const token = localStorage.getItem("token");
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    
    const merged = { ...headers, ...options.headers};

    const response = await fetch(`${BASE_URL}${path}`, {...options, headers: merged});
    if (!response.ok) {
        const body = await response.json();
        throw new Error(body.detail || "An error occurred while fetching data.");
    }
    return response.json();
}
