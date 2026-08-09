import { Link, useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import type { FormEvent } from "react"
import { useNavigate } from "react-router-dom";
import apiFetch from "../api";
import Layout from "../components/Layout";

const inputClass =
    "w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500";

type MaintenanceType = {
    maintenance_type_id: number,
    name: string
}

function LogServicePage() {
    const { carId } = useParams<{ carId: string }>()
    const [maintenanceTypes, setMaintenanceTypes] = useState<MaintenanceType[]>([]);
    const [maintenanceTypeName, setMaintenanceTypeName] = useState("");
    const [milesAtService, setMilesAtService] = useState("");
    const [date, setDate] = useState("");
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate()


    useEffect(() => {
        async function loadMaintenanceTypes() {
            try {
                const data = await apiFetch("/maintenance_types");
                setMaintenanceTypes(data.maintenance_types);

            } catch (err) {
                setError((err as Error).message);
            }
        }

        loadMaintenanceTypes()
    }, [])

    async function handleSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError(null);

        try {
            const maintData = await apiFetch("/maintenance_type", {
                method: "POST",
                body: JSON.stringify({ name: maintenanceTypeName })
            })

            await apiFetch("/service", {
                method: "POST",
                body: JSON.stringify({
                    car_id: Number(carId),
                    maintenance_type_id: maintData.maintenance_type_id,
                    miles_at_service: Number(milesAtService),
                    date
                })
            })

            navigate(`/cars/${carId}`)

        } catch (err) {
            setError((err as Error).message);
        }
    }
    return (
        <Layout>
            <Link to={`/cars/${carId}`} className="text-sm text-slate-500 hover:text-slate-900">
                &larr; Back to car
            </Link>

            <div className="mx-auto mt-4 max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                <h1 className="text-xl font-semibold text-slate-900">Log a service</h1>
                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    <input
                        list="maintenance-types"
                        value={maintenanceTypeName}
                        onChange={(e) => setMaintenanceTypeName(e.target.value)}
                        placeholder="Maintenance type"
                        className={inputClass}
                    />
                    <datalist id="maintenance-types">
                        {maintenanceTypes.map((mt) => (
                            <option key={mt.maintenance_type_id} value={mt.name} />

                        ))}
                    </datalist>

                    <input value={milesAtService} onChange={(e) => setMilesAtService(e.target.value)} placeholder="Miles at service" className={inputClass} />
                    <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className={inputClass} />
                    <button type="submit" className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">
                        Log Service
                    </button>
                    {error && <p className="text-sm text-red-600">{error}</p>}
                </form>
            </div>
        </Layout>
    );
}


export default LogServicePage;
