import { useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

function BotConfig() {
  const [platform, setPlatform] = useState('telegram')
  const [token, setToken] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const clientId = localStorage.getItem('clientId')
  const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: { 'X-Client-Id': clientId || '', 'X-Admin-Api-Key': 'dev-key' }
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!clientId) {
      setMessage('Please login first')
      return
    }

    setLoading(true)
    try {
      await api.post('/admin/bots/add', {
        platform,
        token,
        name
      })
      setMessage('Bot added successfully!')
      setToken('')
      setName('')
    } catch (err) {
      setMessage('Failed to add bot. Check your token.')
    } finally {
      setLoading(false)
    }
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
            <Link to="/dashboard" className="text-slate-400 hover:text-white">← Back to Dashboard</Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-24 pb-12 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Bot Configuration</h1>
        <p className="text-slate-400 mb-8">Add a new bot to your agent</p>

        <div className="glass rounded-2xl p-8 border border-slate-800">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Platform Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Platform</label>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-violet-500"
              >
                <option value="telegram">Telegram</option>
                <option value="twilio_sms">SMS (Twilio)</option>
                <option value="twilio_voice">Voice (Twilio)</option>
                <option value="email">Email</option>
              </select>
            </div>

            {/* Bot Name */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Bot Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Sales Bot"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500"
                required
              />
            </div>

            {/* Token */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                {platform === 'telegram' ? 'Bot Token (from @BotFather)' : 'API Token'}
              </label>
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Enter your token"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500"
                required
              />
              <p className="text-slate-500 text-sm mt-2">
                {platform === 'telegram' 
                  ? 'Get this from @BotFather on Telegram'
                  : 'Your Twilio/API credentials'}
              </p>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-violet-600 hover:bg-violet-700 disabled:bg-slate-700 py-3 rounded-lg font-semibold transition"
            >
              {loading ? 'Adding...' : 'Add Bot'}
            </button>

            {message && (
              <div className={`p-4 rounded-lg ${message.includes('success') ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {message}
              </div>
            )}
          </form>
        </div>

        {/* Instructions */}
        <div className="mt-8 glass rounded-2xl p-6 border border-slate-800">
          <h3 className="font-semibold mb-4">Platform Setup Guides</h3>
          <div className="space-y-4 text-sm text-slate-400">
            <details>
              <summary className="cursor-pointer hover:text-white">Telegram Setup</summary>
              <ol className="mt-2 ml-4 space-y-1 list-decimal">
                <li>Message @BotFather on Telegram</li>
                <li>Create a new bot with /newbot</li>
                <li>Copy the token provided</li>
                <li>Paste it above</li>
              </ol>
            </details>
            <details>
              <summary className="cursor-pointer hover:text-white">Twilio Setup</summary>
              <ol className="mt-2 ml-4 space-y-1 list-decimal">
                <li>Sign up at twilio.com</li>
                <li>Get your Account SID and Auth Token</li>
                <li>Buy a phone number</li>
                <li>Enter credentials above</li>
              </ol>
            </details>
          </div>
        </div>
      </main>
    </div>
  )
}

export default BotConfig
