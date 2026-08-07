import { Routes, Route } from 'react-router-dom'
import SignupPage from './pages/SignupPage.tsx'
import LoginPage from './pages/LoginPage.tsx'
import CarsDashboard from './pages/CarsDashboard.tsx'
import CarDetailPage from './pages/CarDetailPage.tsx'



function App() {
  return (
    <Routes>
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/cars" element={<CarsDashboard />} />
      <Route path="/cars/:carId" element={<CarDetailPage />} />
    </Routes>
  )
}

export default App
