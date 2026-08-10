import { Link, useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import apiFetch from '../api';
import type { Car } from './CarsDashboard';
import Layout from '../components/Layout';

type Part = {
    part_id: number;
    name: string;
    brand: string;
    price_at_service_cents: number | null;
}


type Service = {
    service_id: number;
    maintenance_type_id: number;
    maintenance_name: string;
    miles_at_service: number;
    date: string;
    parts: Part[];
}


function CarDetailPage() {

    const { carId } = useParams<{ carId: string }>();
    const navigate = useNavigate();
    const [car, setCar] = useState<Car | null>(null);
    const [services, setServices] = useState<Service[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadData() {
            try {
                const carData = await apiFetch(`/cars/${carId}`);
                setCar(carData);
                const servicesData = await apiFetch(`/cars/${carId}/services`);
                setServices(servicesData.services);


            } catch (err) {
                setError((err as Error).message);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, [carId]);

    if (loading) {
        return (
            <Layout>
                <p className="text-slate-500">Loading...</p>
            </Layout>
        );
    }

    if (error) {
        return (
            <Layout>
                <p className="text-red-600">Error: {error}</p>
            </Layout>
        );
    }

    if (!car) {
        return (
            <Layout>
                <p className="text-slate-500">Car not found</p>
            </Layout>
        );
    }

    async function handleDeleteService(serviceId: number) {
        if (!window.confirm("Delete this service?")){
            return;
        }
        try {
            await apiFetch(`/service/${serviceId}`, { method: "DELETE" });
            setServices(services.filter((service) => service.service_id !== serviceId));
        } catch (err) {
            setError((err as Error).message);
        }
    }

    async function handleDeleteCar() {
        if (!window.confirm("Delete this car? This will also delete its entire service history.")) {
            return;
        }
        try {
            await apiFetch(`/car/${carId}`, { method: "DELETE" });
            navigate("/cars");
        } catch (err) {
            setError((err as Error).message);
        }
    }

    async function handleDeletePart(serviceId: number, partId: number) {
        if (!window.confirm("Remove this part from the service?")) {
            return;
        }
        try {
            await apiFetch(`/service_part/${serviceId}/${partId}`, { method: "DELETE" });
            setServices(services.map((service) => {
                if (service.service_id !== serviceId) {
                    return service;
                }
                return {
                    ...service,
                    parts: service.parts.filter((part) => part.part_id !== partId),
                };
            }));
        } catch (err) {
            setError((err as Error).message);
        }
    }

    return (
        <Layout>
            <Link to="/cars" className="text-sm text-slate-500 hover:text-slate-900">
                &larr; Back to your cars
            </Link>

            <div className="mt-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-start justify-between">
                    <h1 className="text-2xl font-semibold text-slate-900">
                        {car.year} {car.make} {car.model}
                    </h1>
                    <button
                        onClick={handleDeleteCar}
                        className="text-sm font-medium text-red-600 hover:text-red-800"
                    >
                        Delete Car
                    </button>
                </div>
                <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-slate-500">
                    <dt>VIN</dt>
                    <dd className="text-slate-700">{car.vin ?? "Not on file"}</dd>
                    <dt>Total miles</dt>
                    <dd className="text-slate-700">
                        {car.total_miles !== null ? car.total_miles.toLocaleString() : "Unknown"}
                    </dd>
                </dl>
            </div>

            <div className="mt-8 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">Service History</h2>
                <Link
                    to={`/cars/${carId}/services/new`}
                    className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
                >
                    Log Service
                </Link>
            </div>

            {services.length === 0 ? (
                <p className="mt-4 text-slate-500">No services logged yet.</p>
            ) : (
                <ul className="mt-4 space-y-4">
                    {services.map((service) => (
                        <li
                            key={service.service_id}
                            className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="font-medium text-slate-900">{service.maintenance_name}</p>
                                    <p className="text-sm text-slate-500">
                                        {service.date} &middot; {service.miles_at_service.toLocaleString()} miles
                                    </p>
                                </div>
                                <Link
                                    to={`/cars/${carId}/services/${service.service_id}/parts/new`}
                                    className="text-sm font-medium text-slate-500 hover:text-slate-900"
                                >
                                    + Attach Part
                                </Link>
                            </div>
                            <button
                                onClick={() => handleDeleteService(service.service_id)}
                                className="mt-2 text-sm font-medium text-red-600 hover:text-red-800"
                            >
                                Delete Service
                            </button>
                            {service.parts.length > 0 && (
                                <ul className="mt-3 space-y-1 border-t border-slate-100 pt-3">
                                    {service.parts.map((part) => (
                                        <li
                                            key={part.part_id}
                                            className="flex items-center justify-between text-sm text-slate-600"
                                        >
                                            <span>
                                                {part.name} ({part.brand})
                                                {part.price_at_service_cents !== null &&
                                                    ` — $${(part.price_at_service_cents / 100).toFixed(2)}`}
                                            </span>
                                            <button
                                                onClick={() => handleDeletePart(service.service_id, part.part_id)}
                                                className="text-xs font-medium text-red-600 hover:text-red-800"
                                            >
                                                Remove
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </Layout>
    );
}

export default CarDetailPage;
