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
        <form onSubmit={handleSubmit}>
            <input
                list="maintenance-types"
                value={maintenanceTypeName}
                onChange={(e) => setMaintenanceTypeName(e.target.value)}
                placeholder="Maintenance type"
            />
            <datalist id="maintenance-types">
                {maintenanceTypes.map((mt) => (
                    <option key={mt.maintenance_type_id} value={mt.name} />

                ))}
            </datalist>


            <input value={milesAtService} onChange={(e) => setMilesAtService(e.target.value)} placeholder="Miles at Service" />
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <button type="submit">Log Service</button>
            {error && <p>{error}</p>}
        </form>
    );
}


export default LogServicePage;