import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

interface Bot {
  id: string
  platform: string
  status: string
}

function Dashboard() {
  const [credits, setCredits] = useState<number | null>(null)
  const [bots, setBots] = useState<Bot[]>([])
  const [loading, setLoading] = useState(true)

  const clientId = localStorage.getItem('clientId')
  const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: { 'X-Client-Id': clientId || '' }
  })

  useEffect(() => {
    if (!clientId) return
    
    const fetchData = async () => {
      try {
        const [creditsRes, botsRes] = await Promise.all([
          api.get('/credits/balance'),
          api.get('/admin/bots/status')
        ])
        setCredits(creditsRes.data.balance)
        setBots(botsRes.data.bots || [])
      } catch (err) {
        console.error('Failed to fetch data', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [clientId])

  if (!clientId) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400 mb-4">Please sign in first</p>
          <Link to="/login" className="bg-violet-600 hover:bg-violet-700 px-6 py-3 rounded-lg font-medium">
            Go to Login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <nav className="glass fixed w-full z-50 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-lg"></div>
              <span className="font-bold text-xl">AI Agent Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/credits" className="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg text-sm">
                Credits: {loading ? '...' : credits}
              </Link>
              <span className="text-slate-400 text-sm">{clientId}</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-24 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="glass rounded-2xl p-6 border border-slate-800">
            <h3 className="text-slate-400 text-sm mb-2">Available Credits</h3>
            <div className="text-3xl font-bold">{loading ? '-' : credits}</div>
          </div>
          <div className="glass rounded-2xl p-6 border border-slate-800">
            <h3 className="text-slate-400 text-sm mb-2">Active Bots</h3>
            <div className="text-3xl font-bold">{bots.length}</div>
          </div>
          <div className="glass rounded-2xl p-6 border border-slate-800">
            <h3 className="text-slate-400 text-sm mb-2">Status</h3>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="font-medium">Active</span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="glass rounded-2xl p-6 border border-slate-800 mb-8">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="flex flex-wrap gap-4">
            <Link to="/bot-config" className="bg-violet-600 hover:bg-violet-700 px-6 py-3 rounded-lg font-medium transition">
              + Add Bot
            </Link>
            <Link to="/credits" className="bg-slate-800 hover:bg-slate-700 px-6 py-3 rounded-lg font-medium transition">
              Buy Credits
            </Link>
            <Link to="/setup" className="border border-slate-700 hover:border-slate-600 px-6 py-3 rounded-lg font-medium transition">
              Setup Wizard
            </Link>
          </div>
        </div>

        {/* Bot List */}
        <div className="glass rounded-2xl border border-slate-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800">
            <h2 className="text-xl font-semibold">Your Bots</h2>
          </div>
          {bots.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              <p>No bots configured yet.</p>
              <Link to="/bot-config" className="text-violet-400 hover:text-violet-300 mt-2 inline-block">
                Add your first bot →
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {bots.map((bot) => (
                <div key={bot.id} className="px-6 py-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium">{bot.platform}</p>
                    <p className="text-slate-400 text-sm">{bot.id}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    bot.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-slate-700 text-slate-400'
                  }`}>
                    {bot.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default Dashboard
