import { Link, useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import type { FormEvent } from "react"
import { useNavigate } from "react-router-dom";
import apiFetch from "../api";
import Layout from "../components/Layout";

const inputClass =
    "w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500";

type PartType = {
    part_id: number,
    name: string,
    brand: string
}

function AttachPartPage() {

    const  {carId, serviceId} = useParams<{ carId: string; serviceId: string }>()
    const [parts, setParts] = useState<PartType[]>([]);
    const [partName, setPartName] = useState("");
    const [brand, setBrand] = useState("");
    const [priceAtService, setPriceAtService] = useState("");
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        async function loadPartTypes() {
            try {
                const data = await apiFetch("/parts");
                setParts(data.parts)
            } catch (err) {
                setError((err as Error).message);
            }
        }

        loadPartTypes()

    }, [])

    async function handleSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError(null);

        try {
            const pData = await apiFetch("/part", {
                method: "POST",
                body: JSON.stringify({
                    name: partName,
                    brand: brand
                 })
            })

            await apiFetch("/service_part", {
                method: "POST",
                body: JSON.stringify({
                    service_id: Number(serviceId),
                    price_at_service_cents: priceAtService === "" ? undefined : Number(priceAtService),
                    part_id: Number(pData.part_id)
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
                <h1 className="text-xl font-semibold text-slate-900">Attach a part</h1>
                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    <input
                        list="part-types"
                        value={(partName)}
                        onChange={(e) => setPartName(e.target.value)}
                        placeholder="Part type"
                        className={inputClass}
                    />
                    <datalist id="part-types">
                        {parts.map((pt) => (
                            <option key={pt.part_id} value={pt.name} />
                        ))}
                    </datalist>
                    <input
                        list="brand-types"
                        value={(brand)}
                        onChange={(e) => setBrand(e.target.value)}
                        placeholder="Brand (or Unknown)"
                        className={inputClass}
                    />
                    <datalist id="brand-types">
                        {parts.map((pt) => (
                            <option key={pt.part_id} value={pt.brand} />
                        ))}
                    </datalist>

                    <input type="number" placeholder="Price at Service (optional)" value={priceAtService} onChange={(e) => setPriceAtService(e.target.value)} className={inputClass} />
                    <button type="submit" className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">
                        Attach Part
                    </button>
                    {error && <p className="text-sm text-red-600">{error}</p>}
                </form>
            </div>
        </Layout>
    )

}

export default AttachPartPage;
