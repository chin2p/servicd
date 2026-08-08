import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import type { FormEvent } from "react"
import { useNavigate } from "react-router-dom";
import apiFetch from "../api";

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
        <form onSubmit={handleSubmit}>

            <input
                list="part-types"
                value={(partName)}
                onChange={(e) => setPartName(e.target.value)}
                placeholder="Part type"
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
            />
            <datalist id="brand-types">
                {parts.map((pt) => (
                    <option key={pt.part_id} value={pt.brand} />
                ))}
            </datalist>
            
            <input type="number" placeholder="Price at Service (optional)" value={priceAtService} onChange={(e) => setPriceAtService(e.target.value)} />
            <button type="submit">Log Part</button>
            {error && <p>{error}</p>}
        
        
        </form>

    )

}

export default AttachPartPage;