import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

function Login() {
  const [clientId, setClientId] = useState('')
  const navigate = useNavigate()

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    // Store client ID in localStorage for API calls
    localStorage.setItem('clientId', clientId)
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
      <div className="glass rounded-2xl p-8 border border-slate-800 w-full max-w-md mx-4">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-lg mx-auto mb-4"></div>
          <h1 className="text-2xl font-bold">Welcome Back</h1>
          <p className="text-slate-400">Enter your Client ID to continue</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Client ID</label>
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="e.g., client_abc123"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-violet-600 hover:bg-violet-700 py-3 rounded-lg font-semibold transition"
          >
            Sign In
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-slate-400 text-sm">
            Don't have an account?{' '}
            <Link to="/setup" className="text-violet-400 hover:text-violet-300">
              Create Agent
            </Link>
          </p>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 text-center">
          <Link to="/" className="text-slate-500 hover:text-slate-400 text-sm">
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Login
