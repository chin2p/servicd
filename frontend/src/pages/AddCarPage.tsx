import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import apiFetch from "../api";





function AddCarPage() {

    const [step, setStep] = useState(1);
    const [year, setYear] = useState('');
    const [make, setMake] = useState('');
    const [model, setModel] = useState('');
    const [engine, setEngine] = useState('');
    const [vin, setVin] = useState('');
    const [configId, setConfigId] = useState<number | null>(null);
    const [totalMiles, setTotalMiles] = useState('');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    async function handleConfigSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault(); setError(null);
        try {
            const data = await apiFetch('/car_config', {
                method: 'POST',
                body: JSON.stringify({ year: Number(year), make, model, engine }),
            })
            setConfigId(data.config_id);
            setStep(2);

        } catch (err) {
            setError((err as Error).message);
        }
    }
    async function handleCarSubmit(e: FormEvent<HTMLFormElement>) {
        
        e.preventDefault(); 
        setError(null);
        
        try {
            await apiFetch("/car", {
                method: "POST",
                body: JSON.stringify({
                    config_id: configId,
                    vin: vin === "" ? undefined : vin,
                    total_miles: totalMiles === "" ? undefined : Number(totalMiles)

                })
                
            })
            navigate("/cars")
        } catch (err) {
            setError((err as Error).message);
        }
    }

    if (step === 1) {
        return (
            <form onSubmit={handleConfigSubmit}>
                <input value={year} onChange={(e) => setYear(e.target.value)} placeholder="Year" />
                <input value={make} onChange={(e) => setMake(e.target.value)} placeholder="Make" />
                <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="Model" />
                <input value={engine} onChange={(e) => setEngine(e.target.value)} placeholder="Engine (optional)" />
                <button type="submit">Next</button>
                {error && <p>{error}</p>}
            </form>
        );
    }

    return (
        <form onSubmit={handleCarSubmit}>
            <input value={vin} onChange={(e) => setVin(e.target.value)} placeholder="VIN (optional)" />
            <input value={totalMiles} onChange={(e) => setTotalMiles(e.target.value)} placeholder="Total miles (optional)" />
            <button type="submit">Add Car</button>
            {error && <p>{error}</p>}
        </form>
    );

}

export default AddCarPage;