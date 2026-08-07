import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import type { FormEvent } from "react"
import { useNavigate } from "react-router-dom";
import apiFetch from "../api";

type MaintenanceType = {
    maintenance_type_id: number,
    name: string
}

function LogServicePage() {
    const { carId } = useParams<{ carId: string }>()
    const [maintenanceTypes, setMaintenanceTypes] = useState<MaintenanceType[]>([]);
    const [maintenanceTypeId, setMaintenanceTypeId] = useState("");
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
            await apiFetch("/service", {
                method: "POST",
                body: JSON.stringify({
                    car_id: Number(carId),
                    maintenance_type_id: Number(maintenanceTypeId),
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
        <form onSubmit={handleSubmit}>
            <select value={maintenanceTypeId} onChange={(e) => setMaintenanceTypeId(e.target.value)}>
                <option value="">Select maintenance type</option>
                
                {maintenanceTypes.map((mt) => (
                    <option key={mt.maintenance_type_id} value={mt.maintenance_type_id}>{mt.name}</option>
                ))}

            </select>
            <input value={milesAtService} onChange={(e) => setMilesAtService(e.target.value)} placeholder="Miles at Service" />
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <button type="submit">Log Service</button>
            {error && <p>{error}</p>}
        </form>
    );
}


export default LogServicePage;