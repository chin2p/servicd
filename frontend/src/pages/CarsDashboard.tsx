import { useEffect, useState } from "react";
import apiFetch from "../api";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";

export type Car = {
    car_id: number;
    vin: string;
    total_miles: number | null;
    year: number;
    make: string;
    model: string;
    engine: string;
};

function CarsDashboard() {

    const [cars, setCars] = useState<Car[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadCars() {
            try {
                const data = await apiFetch("/cars");
                setCars(data.cars);
            } catch (err) {
                setError((err as Error).message);

            } finally {
                setLoading(false);
            }
        }
        loadCars();
        }, []);

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

        return (
            <Layout>
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-semibold text-slate-900">Your Cars</h1>
                    <Link
                        to="/cars/new"
                        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
                    >
                        Add Car
                    </Link>
                </div>

                {cars.length === 0 ? (
                    <p className="mt-8 text-slate-500">
                        You haven't added any cars yet.
                    </p>
                ) : (
                    <ul className="mt-6 grid gap-4 sm:grid-cols-2">
                        {cars.map((car) => (
                            <li key={car.car_id}>
                                <Link
                                    to={`/cars/${car.car_id}`}
                                    className="block rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300 hover:shadow-md"
                                >
                                    <p className="font-medium text-slate-900">
                                        {car.year} {car.make} {car.model}
                                    </p>
                                    <p className="mt-1 text-sm text-slate-500">
                                        {car.vin ?? "No VIN on file"}
                                    </p>
                                    {car.total_miles !== null && (
                                        <p className="mt-1 text-sm text-slate-500">
                                            {car.total_miles.toLocaleString()} miles
                                        </p>
                                    )}
                                </Link>
                            </li>
                        ))}
                    </ul>
                )}
            </Layout>
        );

}

export default CarsDashboard;
