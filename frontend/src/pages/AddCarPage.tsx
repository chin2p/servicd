import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import apiFetch from "../api";
import Layout from "../components/Layout";

const inputClass =
    "w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500";
const buttonClass =
    "w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700";
const secondaryButtonClass =
    "w-full rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-100";
const cancelLinkClass = "block text-center text-sm text-slate-500 hover:text-slate-900";

function AddCarPage() {

    const [step, setStep] = useState(1);
    const [year, setYear] = useState('');
    const [make, setMake] = useState('');
    const [model, setModel] = useState('');
    const [engine, setEngine] = useState('');
    const [vin, setVin] = useState('');
    const [configId, setConfigId] = useState<number | null>(null);
    const [decoding, setDecoding] = useState(false)
    const [totalMiles, setTotalMiles] = useState('');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();


    async function handleDecode(){
        setError(null); setDecoding(true);

        try {

            const data = await apiFetch(`/vin/${vin}/decode`)
            setYear(String(data.year)); setMake(data.make); setModel(data.model); setEngine(data.engine);
            setStep(2);

        } catch (err) {
            setError((err as Error).message);
        } finally {
            setDecoding(false);
        }

    }

    function handleSkip(){
        setError(null);
        setStep(2)
    }



    async function handleConfigSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault(); setError(null);
        try {
            const data = await apiFetch('/car_config', {
                method: 'POST',
                body: JSON.stringify({ year: Number(year), make, model, engine }),
            })
            setConfigId(data.config_id);
            setStep(3);

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
                    <p className="text-sm font-medium text-slate-400">Step 1 of 3</p>
                    <h1 className="mt-1 text-xl font-semibold text-slate-900">Know your VIN?</h1>
                    <p className="mt-1 text-sm text-slate-500">
                        We can auto-fill your car's details from its VIN, or you can enter them manually.
                    </p>
                    <div className="mt-6 space-y-4">
                        <input
                            value={vin}
                            onChange={(e) => setVin(e.target.value)}
                            placeholder="VIN"
                            className={inputClass}
                        />
                        <button
                            type="button"
                            onClick={handleDecode}
                            disabled={vin === "" || decoding}
                            className={`${buttonClass} disabled:cursor-not-allowed disabled:opacity-50`}
                        >
                            {decoding ? "Decoding..." : "Decode"}
                        </button>
                        <button type="button" onClick={handleSkip} className={secondaryButtonClass}>
                            Skip, I'll enter manually
                        </button>
                        {error && <p className="text-sm text-red-600">{error}</p>}
                        <Link to="/cars" className={cancelLinkClass}>
                            Cancel
                        </Link>
                    </div>
                </div>
            </Layout>
        );
    }

    if (step === 2) {
        return (
            <Layout>
                <div className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                    <p className="text-sm font-medium text-slate-400">Step 2 of 3</p>
                    <h1 className="mt-1 text-xl font-semibold text-slate-900">What are you driving?</h1>
                    <form onSubmit={handleConfigSubmit} className="mt-6 space-y-4">
                        <input value={year} onChange={(e) => setYear(e.target.value)} placeholder="Year" required className={inputClass} />
                        <input value={make} onChange={(e) => setMake(e.target.value)} placeholder="Make" required className={inputClass} />
                        <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="Model" required className={inputClass} />
                        <input value={engine} onChange={(e) => setEngine(e.target.value)} placeholder="Engine (optional)" className={inputClass} />
                        <button type="submit" className={buttonClass}>Next</button>
                        {error && <p className="text-sm text-red-600">{error}</p>}
                        <Link to="/cars" className={cancelLinkClass}>
                            Cancel
                        </Link>
                    </form>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                <p className="text-sm font-medium text-slate-400">Step 3 of 3</p>
                <h1 className="mt-1 text-xl font-semibold text-slate-900">A few more details</h1>
                <form onSubmit={handleCarSubmit} className="mt-6 space-y-4">
                    <input value={vin} onChange={(e) => setVin(e.target.value)} placeholder="VIN (optional)" className={inputClass} />
                    <input value={totalMiles} onChange={(e) => setTotalMiles(e.target.value)} placeholder="Total miles (optional)" className={inputClass} />
                    <button type="submit" className={buttonClass}>Add Car</button>
                    {error && <p className="text-sm text-red-600">{error}</p>}
                    <Link to="/cars" className={cancelLinkClass}>
                        Cancel
                    </Link>
                </form>
            </div>
        </Layout>
    );

}

export default AddCarPage;
