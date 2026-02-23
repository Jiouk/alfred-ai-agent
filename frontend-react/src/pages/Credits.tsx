import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

interface Transaction {
  id: string
  type: string
  amount: number
  created_at: string
}

function Credits() {
  const [balance, setBalance] = useState<number | null>(null)
  const [history, setHistory] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)

  const clientId = localStorage.getItem('clientId')
  const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: { 'X-Client-Id': clientId || '' }
  })

  const tiers = [
    { id: 'starter', name: 'Starter', price: 9, credits: 100, popular: false },
    { id: 'growth', name: 'Growth', price: 29, credits: 500, popular: true },
    { id: 'enterprise', name: 'Enterprise', price: 99, credits: 2000, popular: false },
  ]

  useEffect(() => {
    if (!clientId) return

    const fetchData = async () => {
      try {
        const [balanceRes, historyRes] = await Promise.all([
          api.get('/credits/balance'),
          api.get('/credits/history')
        ])
        setBalance(balanceRes.data.balance)
        setHistory(historyRes.data.transactions || [])
      } catch (err) {
        console.error('Failed to fetch data', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [clientId])

  const handlePurchase = async (tierId: string) => {
    if (!clientId) return
    
    try {
      const res = await api.post('/credits/purchase', { tier: tierId })
      if (res.data.checkout_url) {
        window.location.href = res.data.checkout_url
      }
    } catch (err) {
      console.error('Purchase failed', err)
    }
  }

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
            <Link to="/dashboard" className="text-slate-400 hover:text-white">← Back to Dashboard</Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-24 pb-12 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        {/* Balance Card */}
        <div className="glass rounded-2xl p-8 border border-slate-800 mb-8 text-center">
          <p className="text-slate-400 mb-2">Current Balance</p>
          <div className="text-5xl font-bold gradient-text">
            {loading ? '-' : balance} credits
          </div>
        </div>

        {/* Purchase Tiers */}
        <h2 className="text-2xl font-bold mb-6">Buy Credits</h2>
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {tiers.map((tier) => (
            <div
              key={tier.id}
              className={`glass rounded-2xl p-6 border ${tier.popular ? 'border-violet-500 relative' : 'border-slate-800'}`}
            >
              {tier.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-violet-600 text-xs font-semibold px-3 py-1 rounded-full">
                  POPULAR
                </div>
              )}
              <h3 className="text-lg font-medium text-slate-400 mb-2">{tier.name}</h3>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-bold">€{tier.price}</span>
              </div>
              <div className="text-2xl font-semibold mb-4">{tier.credits} credits</div>
              <ul className="text-slate-400 text-sm mb-6 space-y-2">
                <li>✓ ~{Math.round(tier.credits / 10)} conversations</li>
                <li>✓ All features included</li>
                <li>✓ Never expires</li>
              </ul>
              <button
                onClick={() => handlePurchase(tier.id)}
                className={`w-full py-3 rounded-lg font-semibold transition ${
                  tier.popular
                    ? 'bg-violet-600 hover:bg-violet-700'
                    : 'border border-slate-700 hover:border-slate-600'
                }`}
              >
                Purchase
              </button>
            </div>
          ))}
        </div>

        {/* Transaction History */}
        <h2 className="text-2xl font-bold mb-6">Transaction History</h2>
        <div className="glass rounded-2xl border border-slate-800 overflow-hidden">
          {history.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              No transactions yet
            </div>
          ) : (
            <table className="w-full">
              <thead className="border-b border-slate-800">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Date</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-400">Type</th>
                  <th className="px-6 py-4 text-right text-sm font-medium text-slate-400">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {history.map((tx) => (
                  <tr key={tx.id}>
                    <td className="px-6 py-4 text-sm">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm capitalize">{tx.type}</td>
                    <td className={`px-6 py-4 text-sm text-right ${tx.amount > 0 ? 'text-green-400' : 'text-slate-300'}`}>
                      {tx.amount > 0 ? '+' : ''}{tx.amount}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  )
}

export default Credits
