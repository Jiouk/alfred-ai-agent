import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import axios from 'axios'

function SetupWizard() {
  const [step, setStep] = useState(1)
  const [botName, setBotName] = useState('')
  const [purpose, setPurpose] = useState('sales')
  const [personality, setPersonality] = useState('professional')
  const [platform, setPlatform] = useState('telegram')
  const [token, setToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [clientId, setClientId] = useState('')

  const navigate = useNavigate()

  const handleComplete = async () => {
    setLoading(true)
    try {
      // Create agent via API
      const res = await axios.post('http://localhost:8000/onboarding/claim-agent', {
        bot_name: botName,
        purpose,
        personality,
        platform,
        token
      })
      
      // Store client ID and redirect
      localStorage.setItem('clientId', res.data.client_id)
      setClientId(res.data.client_id)
      setStep(4) // Success step
    } catch (err) {
      console.error('Setup failed', err)
      alert('Setup failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const goToDashboard = () => {
    navigate('/dashboard')
  }

  const steps = [
    { num: 1, label: 'Basics' },
    { num: 2, label: 'Channel' },
    { num: 3, label: 'Connect' },
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Progress */}
        {step < 4 && (
          <div className="flex items-center justify-center space-x-4 mb-10">
            {steps.map((s, i) => (
              <div key={s.num} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  step >= s.num ? 'bg-violet-600' : 'bg-slate-800 border border-slate-700'
                }`}>
                  {s.num}
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-16 h-1 mx-2 ${step > s.num ? 'bg-violet-600' : 'bg-slate-800'}`}></div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="glass rounded-2xl p-8 border border-slate-800">
          {/* Step 1: Basics */}
          {step === 1 && (
            <>
              <h1 className="text-2xl font-bold mb-2">Create Your AI Agent</h1>
              <p className="text-slate-400 mb-8">Step 1 of 3 — Let's start with the basics</p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">What should we call your bot?</label>
                  <input
                    type="text"
                    value={botName}
                    onChange={(e) => setBotName(e.target.value)}
                    placeholder="e.g., Sales Assistant"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">What's its main job?</label>
                  <select
                    value={purpose}
                    onChange={(e) => setPurpose(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="sales">Sales & Lead Generation</option>
                    <option value="support">Customer Support</option>
                    <option value="booking">Appointment Booking</option>
                    <option value="assistant">General Assistant</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Personality</label>
                  <div className="grid grid-cols-2 gap-4">
                    {['professional', 'friendly', 'witty', 'concise'].map((p) => (
                      <label
                        key={p}
                        className={`flex items-center space-x-3 p-4 border rounded-lg cursor-pointer transition ${
                          personality === p
                            ? 'border-violet-500 bg-violet-500/10'
                            : 'border-slate-700 bg-slate-900 hover:border-slate-600'
                        }`}
                      >
                        <input
                          type="radio"
                          name="personality"
                          value={p}
                          checked={personality === p}
                          onChange={(e) => setPersonality(e.target.value)}
                          className="text-violet-600"
                        />
                        <span className="capitalize">{p}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-between mt-8">
                <Link to="/" className="text-slate-400 hover:text-white transition">Cancel</Link>
                <button
                  onClick={() => setStep(2)}
                  disabled={!botName}
                  className="bg-violet-600 hover:bg-violet-700 disabled:bg-slate-700 px-6 py-3 rounded-lg font-semibold transition"
                >
                  Continue →
                </button>
              </div>
            </>
          )}

          {/* Step 2: Channel */}
          {step === 2 && (
            <>
              <h1 className="text-2xl font-bold mb-2">Choose Your Channel</h1>
              <p className="text-slate-400 mb-8">Step 2 of 3 — Where will your agent live?</p>

              <div className="grid grid-cols-2 gap-4">
                {[
                  { id: 'telegram', name: 'Telegram', icon: '💬' },
                  { id: 'sms', name: 'SMS', icon: '💬' },
                  { id: 'voice', name: 'Voice', icon: '📞' },
                  { id: 'email', name: 'Email', icon: '✉️' },
                ].map((ch) => (
                  <button
                    key={ch.id}
                    onClick={() => setPlatform(ch.id)}
                    className={`p-6 border rounded-xl text-left transition ${
                      platform === ch.id
                        ? 'border-violet-500 bg-violet-500/10'
                        : 'border-slate-700 bg-slate-900 hover:border-slate-600'
                    }`}
                  >
                    <span className="text-3xl mb-2 block">{ch.icon}</span>
                    <span className="font-semibold">{ch.name}</span>
                  </button>
                ))}
              </div>

              <div className="flex justify-between mt-8">
                <button onClick={() => setStep(1)} className="text-slate-400 hover:text-white transition">← Back</button>
                <button onClick={() => setStep(3)} className="bg-violet-600 hover:bg-violet-700 px-6 py-3 rounded-lg font-semibold transition">
                  Continue →
                </button>
              </div>
            </>
          )}

          {/* Step 3: Connect */}
          {step === 3 && (
            <>
              <h1 className="text-2xl font-bold mb-2">Connect {platform === 'telegram' ? 'Telegram' : platform}</h1>
              <p className="text-slate-400 mb-8">Step 3 of 3 — Add your credentials</p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {platform === 'telegram' ? 'Bot Token' : 'API Token'}
                  </label>
                  <input
                    type="password"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder={platform === 'telegram' ? 'From @BotFather' : 'Your API key'}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-violet-500"
                  />
                  <p className="text-slate-500 text-sm mt-2">
                    {platform === 'telegram'
                      ? 'Message @BotFather on Telegram to create a bot'
                      : 'Find this in your platform dashboard'}
                  </p>
                </div>
              </div>

              <div className="flex justify-between mt-8">
                <button onClick={() => setStep(2)} className="text-slate-400 hover:text-white transition">← Back</button>
                <button
                  onClick={handleComplete}
                  disabled={!token || loading}
                  className="bg-violet-600 hover:bg-violet-700 disabled:bg-slate-700 px-6 py-3 rounded-lg font-semibold transition"
                >
                  {loading ? 'Creating...' : 'Create Agent ✨'}
                </button>
              </div>
            </>
          )}

          {/* Step 4: Success */}
          {step === 4 && (
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-4xl">🎉</span>
              </div>
              <h1 className="text-2xl font-bold mb-2">Your Agent is Ready!</h1>
              <p className="text-slate-400 mb-6">
                Client ID: <code className="bg-slate-800 px-2 py-1 rounded">{clientId}</code>
              </p>
              <p className="text-slate-400 mb-8">
                Save this ID — you'll need it to login. Your agent is now live on {platform}.
              </p>
              <button
                onClick={goToDashboard}
                className="bg-violet-600 hover:bg-violet-700 px-8 py-3 rounded-lg font-semibold transition"
              >
                Go to Dashboard →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SetupWizard
