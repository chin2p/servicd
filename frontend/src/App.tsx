import { Routes, Route } from 'react-router-dom'
import SignupPage from './pages/SignupPage.tsx'
import LoginPage from './pages/LoginPage.tsx'
import CarsDashboard from './pages/CarsDashboard.tsx'


function App() {
  return (
    <Routes>
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/cars" element={<CarsDashboard />} />
    </Routes>
  )
}

export default App
