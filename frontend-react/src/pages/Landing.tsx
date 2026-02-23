import { Link } from 'react-router-dom'

function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Navigation */}
      <nav className="glass fixed w-full z-50 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-lg"></div>
              <span className="font-bold text-xl">AI Agent Platform</span>
            </div>
            <div className="flex items-center space-x-6">
              <a href="#features" className="text-slate-400 hover:text-white transition">Features</a>
              <a href="#pricing" className="text-slate-400 hover:text-white transition">Pricing</a>
              <Link to="/login" className="bg-violet-600 hover:bg-violet-700 px-4 py-2 rounded-lg font-medium transition">Get Started</Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-900/20 via-slate-950 to-fuchsia-900/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            Your AI Agent<br />
            <span className="gradient-text">In Minutes</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
            Zero-dashboard configuration. Just chat with your agent to set up bots, integrations, and automations.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/setup" className="bg-violet-600 hover:bg-violet-700 px-8 py-4 rounded-xl font-semibold text-lg transition shadow-lg shadow-violet-600/25">
              Create Your Agent
            </Link>
            <a href="#features" className="border border-slate-700 hover:border-slate-600 px-8 py-4 rounded-xl font-semibold transition">
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-16">Everything You Need</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="glass rounded-2xl p-8 border border-slate-800">
              <div className="w-12 h-12 bg-violet-500/20 rounded-xl flex items-center justify-center mb-4 text-2xl">🤖</div>
              <h3 className="text-xl font-semibold mb-2">AI Configuration</h3>
              <p className="text-slate-400">Chat naturally to configure your agent. No complex dashboards.</p>
            </div>
            <div className="glass rounded-2xl p-8 border border-slate-800">
              <div className="w-12 h-12 bg-fuchsia-500/20 rounded-xl flex items-center justify-center mb-4 text-2xl">🔗</div>
              <h3 className="text-xl font-semibold mb-2">Multi-Channel</h3>
              <p className="text-slate-400">Telegram, WhatsApp, SMS, Voice, Email — all in one platform.</p>
            </div>
            <div className="glass rounded-2xl p-8 border border-slate-800">
              <div className="w-12 h-12 bg-cyan-500/20 rounded-xl flex items-center justify-center mb-4 text-2xl">⚡</div>
              <h3 className="text-xl font-semibold mb-2">Pay Per Use</h3>
              <p className="text-slate-400">Buy credits and only pay for what you use. No subscriptions.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 border-t border-slate-800">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-16">Simple Pricing</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="glass rounded-2xl p-8 border border-slate-800">
              <h3 className="text-lg font-medium text-slate-400 mb-2">Starter</h3>
              <div className="text-4xl font-bold mb-4">€9</div>
              <ul className="space-y-3 text-slate-400 mb-8">
                <li>✓ 100 credits</li>
                <li>✓ 1 bot</li>
                <li>✓ Telegram</li>
                <li>✓ Basic support</li>
              </ul>
              <Link to="/credits" className="block text-center border border-slate-700 hover:border-slate-600 py-3 rounded-lg transition">Choose Starter</Link>
            </div>
            <div className="glass rounded-2xl p-8 border-2 border-violet-500 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-violet-600 text-xs font-semibold px-3 py-1 rounded-full">POPULAR</div>
              <h3 className="text-lg font-medium text-slate-400 mb-2">Growth</h3>
              <div className="text-4xl font-bold mb-4">€29</div>
              <ul className="space-y-3 text-slate-400 mb-8">
                <li>✓ 500 credits</li>
                <li>✓ 3 bots</li>
                <li>✓ All channels</li>
                <li>✓ Priority support</li>
              </ul>
              <Link to="/credits" className="block text-center bg-violet-600 hover:bg-violet-700 py-3 rounded-lg transition">Choose Growth</Link>
            </div>
            <div className="glass rounded-2xl p-8 border border-slate-800">
              <h3 className="text-lg font-medium text-slate-400 mb-2">Pay As You Go</h3>
              <div className="text-4xl font-bold mb-4">Custom</div>
              <ul className="space-y-3 text-slate-400 mb-8">
                <li>✓ Flexible credits</li>
                <li>✓ Unlimited bots</li>
                <li>✓ All features</li>
                <li>✓ White-label</li>
              </ul>
              <Link to="/credits" className="block text-center border border-slate-700 hover:border-slate-600 py-3 rounded-lg transition">Contact Sales</Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-500">
          <p>&copy; 2026 AI Agent SaaS Platform. Built with OpenClaw.</p>
        </div>
      </footer>
    </div>
  )
}

export default Landing
