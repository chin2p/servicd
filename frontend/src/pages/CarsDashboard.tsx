import { useEffect, useState } from "react";
import apiFetch from "../api";
import { Link } from "react-router-dom";


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
            return <div>Loading...</div>;
        }

        if (error) {
            return <div>Error: {error}</div>;
        }
        
        return (
            <div>
                <h1>Cars Dashboard</h1>
                <ul>
                    {cars.map((car) => (
                        <li key={car.car_id}>
                            <Link to={`/cars/${car.car_id}`}>
                                {car.year} {car.make} {car.model}
                            </Link>
                        </li>
                    ))}
                </ul>
            </div>
        );

}

export default CarsDashboard;