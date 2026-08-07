import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import apiFetch from '../api';
import type { Car } from './CarsDashboard';




type Service = {
    service_id: number;
    maintenance_type_id: number;
    maintenance_name: string;
    miles_at_service: number;
    date: string;

}

function CarDetailPage() {

    const { carId } = useParams<{ carId: string }>();
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
        return <div>Loading...</div>;
    }
    
    if (error) {
        return <div>Error: {error}</div>;
    }

    if (!car) {
        return <div>Car not found</div>;
    }

    return (
        <div>
            <h1>{car.year} {car.make} {car.model}</h1>
            <p>VIN: {car.vin}</p>
            <p>Total Miles: {car.total_miles}</p>
            <h2>Service History</h2>
            <ul>
                {services.map((service) => (
                    <li key={service.service_id}>
                        {service.date}: {service.maintenance_name} at {service.miles_at_service} miles
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default CarDetailPage;
