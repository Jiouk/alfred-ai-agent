import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import BotConfig from './pages/BotConfig'
import Credits from './pages/Credits'
import SetupWizard from './pages/SetupWizard'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/bot-config" element={<BotConfig />} />
        <Route path="/credits" element={<Credits />} />
        <Route path="/setup" element={<SetupWizard />} />
      </Routes>
    </Router>
  )
}

export default App
