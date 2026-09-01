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

type EditablePart = {
    name: string,
    brand: string,
    priceDollar: string // dollars, as a string for input, converted to cents only at submit time
}
type DecodedPart = {
    name: string,
    brand: string | null,
    price_cents: number | null

}
type DecodedReceipt = {
    maintenance_type: string | null,
    miles_at_service: number | null,
    date: string | null,
    parts: DecodedPart[]
}

function LogServicePage() {
    const { carId } = useParams<{ carId: string }>()
    const [maintenanceTypes, setMaintenanceTypes] = useState<MaintenanceType[]>([]);
    const [maintenanceTypeName, setMaintenanceTypeName] = useState("");
    const [milesAtService, setMilesAtService] = useState("");
    const [date, setDate] = useState("");
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate()
    const [step, setStep] = useState<1 | 2>(1);
    const [receiptFile, setReceiptFile] = useState<File | null>(null);
    const [scanning, setScanning] = useState<true | false>(false);
    const [parts, setParts] = useState<EditablePart[]>([]);



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

            const serviceData = await apiFetch("/service", {
                method: "POST",
                body: JSON.stringify({
                    car_id: Number(carId),
                    maintenance_type_id: maintData.maintenance_type_id,
                    miles_at_service: Number(milesAtService),
                    date
                })
            })
            for (const part of parts) {
                if (part.name === "") {
                    continue
                }
                const partData = await apiFetch("/part", {
                    method: "POST",
                    body: JSON.stringify({
                        name: part.name,
                        brand: part.brand
                    })
                })
                await apiFetch("/service_part", {
                    method: "POST",
                    body: JSON.stringify({
                        service_id: serviceData.service_id,
                        part_id: partData.part_id,
                        price_at_service_cents: part.priceDollar === "" ? undefined : Math.round(Number(part.priceDollar) * 100)
                    })
                })
            }

            navigate(`/cars/${carId}`)

        } catch (err) {
            setError((err as Error).message);
        }
    }

    async function handleScan() {

        if (receiptFile === null) {
            return;
        }
        setScanning(true);
        setError(null);
        const data = new FormData();
        data.append("file", receiptFile);

        try {
            const result: DecodedReceipt = await apiFetch("/receipt/decode", { 
                method: "POST",
                body: data
            })
            setMaintenanceTypeName(result.maintenance_type ?? "");
            setMilesAtService(result.miles_at_service ?.toString() ?? "");
            setDate(result.date ?? "");

            setParts(
                result.parts.map(part => (
                    {
                        name: part.name,
                        brand: part.brand ?? "",
                        priceDollar: part.price_cents != null ? (part.price_cents / 100).toFixed(2) : ""
                    }
                ))
            )
            setStep(2);

        } catch (err) {
            setError((err as Error).message);
        } finally {
            setScanning(false);
        }

    }

    function updatePart(index: number, field: keyof EditablePart, value: string){
        setParts(parts => parts.map((part, i) => i === index ? {...part, [field]: value }: part))
    }

    if (step === 1) {
        return (
            <Layout>
                <Link to={`/cars/${carId}`} className="text-sm text-slate-500 hover:text-slate-900">
                    &larr; Back to car
                </Link>
                
                <div className="mx-auto mt-4 max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                    <h1 className="text-xl font-semibold text-slate-900">Log a service</h1>
                    <div className="mt-6 space-y-4">
                        <input
                            type="file"
                            accept="image/*,application/pdf"
                            onChange={(e) => setReceiptFile(e.target.files?.[0] ?? null)}
                            className={inputClass}
                        />
                        <button
                            type="button"
                            onClick={handleScan}
                            disabled={scanning || receiptFile === null}
                            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {scanning ? "Scanning..." : "Scan receipt"}
                        </button>
                        <button
                            type="button"
                            onClick={() => setStep(2)}
                            className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                            Skip, I'll enter manually
                        </button>
                        {error && <p className="text-sm text-red-600">{error}</p>}
                    </div>
                </div>
            </Layout>
        )
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
                    <section aria-label="Parts">
                        {parts.map((part,index) => (
                            <div key={index}>
                                <input className={inputClass} value={part.name} onChange={(e) => updatePart(index, "name", e.target.value)} placeholder="Part Name"/>
                                <input className={inputClass} value={part.brand} onChange={(e) => updatePart(index, "brand", e.target.value)} placeholder="Part Brand"/>
                                <input className={inputClass} value={part.priceDollar} onChange={(e) => updatePart(index, "priceDollar", e.target.value)} placeholder="Part Price ($)"/>
                            </div>
                        ))}
                    </section>
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
