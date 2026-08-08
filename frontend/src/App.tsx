import { Routes, Route } from 'react-router-dom'
import SignupPage from './pages/SignupPage.tsx'
import LoginPage from './pages/LoginPage.tsx'
import CarsDashboard from './pages/CarsDashboard.tsx'
import CarDetailPage from './pages/CarDetailPage.tsx'
import AddCarPage from './pages/AddCarPage.tsx'
import LogServicePage from './pages/LogServicePage.tsx'
import AttachPartPage from './pages/AttachPartPage.tsx'



function App() {
  return (
    <Routes>
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/cars" element={<CarsDashboard />} />
      <Route path="/cars/:carId" element={<CarDetailPage />} />
      <Route path="/cars/new" element={<AddCarPage />} />
      <Route path="/cars/:carId/services/new" element={<LogServicePage />} />
      <Route path="/cars/:carId/services/:serviceId/parts/new" element={<AttachPartPage />} />
      
    </Routes>
  )
}

export default App
