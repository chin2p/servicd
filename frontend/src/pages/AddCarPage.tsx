import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import apiFetch from "../api";
import Layout from "../components/Layout";

const inputClass =
    "w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500";
const buttonClass =
    "w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700";

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
            <Layout>
                <div className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                    <p className="text-sm font-medium text-slate-400">Step 1 of 2</p>
                    <h1 className="mt-1 text-xl font-semibold text-slate-900">What are you driving?</h1>
                    <form onSubmit={handleConfigSubmit} className="mt-6 space-y-4">
                        <input value={year} onChange={(e) => setYear(e.target.value)} placeholder="Year" className={inputClass} />
                        <input value={make} onChange={(e) => setMake(e.target.value)} placeholder="Make" className={inputClass} />
                        <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="Model" className={inputClass} />
                        <input value={engine} onChange={(e) => setEngine(e.target.value)} placeholder="Engine (optional)" className={inputClass} />
                        <button type="submit" className={buttonClass}>Next</button>
                        {error && <p className="text-sm text-red-600">{error}</p>}
                    </form>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                <p className="text-sm font-medium text-slate-400">Step 2 of 2</p>
                <h1 className="mt-1 text-xl font-semibold text-slate-900">A few more details</h1>
                <form onSubmit={handleCarSubmit} className="mt-6 space-y-4">
                    <input value={vin} onChange={(e) => setVin(e.target.value)} placeholder="VIN (optional)" className={inputClass} />
                    <input value={totalMiles} onChange={(e) => setTotalMiles(e.target.value)} placeholder="Total miles (optional)" className={inputClass} />
                    <button type="submit" className={buttonClass}>Add Car</button>
                    {error && <p className="text-sm text-red-600">{error}</p>}
                </form>
            </div>
        </Layout>
    );

}

export default AddCarPage;
