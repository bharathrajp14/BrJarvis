import Link from 'next/link';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {/* NAVBAR */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-white/10 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🚀</span>
          <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">OnboardAI</span>
        </div>
        <div className="hidden md:flex gap-8 text-sm text-gray-300">
          <a href="#features" className="hover:text-white transition">Features</a>
          <a href="#how" className="hover:text-white transition">How it Works</a>
          <a href="#pricing" className="hover:text-white transition">Pricing</a>
        </div>
        <div className="flex gap-3">
          <Link href="/login" className="px-4 py-2 text-sm text-gray-300 hover:text-white transition">Login</Link>
          <Link href="/register" className="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-500 rounded-lg transition font-medium">Start Free</Link>
        </div>
      </nav>

      {/* HERO */}
      <section className="text-center py-24 px-6">
        <div className="inline-flex items-center gap-2 bg-purple-500/20 border border-purple-500/30 rounded-full px-4 py-1 text-sm text-purple-300 mb-6">
          <span>✨</span> AI-Powered Onboarding Platform
        </div>
        <h1 className="text-5xl md:text-7xl font-extrabold mb-6 leading-tight">
          Onboard Employees
          <span className="block bg-gradient-to-r from-purple-400 via-pink-400 to-orange-400 bg-clip-text text-transparent">
            10x Faster with AI
          </span>
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          OnboardAI automatically generates personalized onboarding plans, assigns tasks, tracks progress, and gets new hires productive from Day 1.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/register" className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 rounded-xl font-bold text-lg transition shadow-lg shadow-purple-500/25">
            Start Free Trial
          </Link>
          <a href="#how" className="px-8 py-4 border border-white/20 hover:border-white/40 rounded-xl font-medium text-lg transition">
            See How It Works
          </a>
        </div>
        <p className="mt-4 text-sm text-gray-500">No credit card required · Free 14-day trial</p>
      </section>

      {/* STATS */}
      <section className="py-12 border-y border-white/10">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center px-6">
          {[['40hrs', 'Saved per hire'],['85%', 'Faster completion'],['10x', 'ROI average'],['500+', 'Companies trust us']].map(([num, label]) => (
            <div key={label}>
              <div className="text-3xl font-extrabold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">{num}</div>
              <div className="text-gray-400 text-sm mt-1">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-4">Everything You Need</h2>
          <p className="text-center text-gray-400 mb-16">One platform to handle your entire onboarding workflow</p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: '🤖', title: 'AI Plan Generator', desc: 'Auto-generates role-specific onboarding plans in seconds using GPT-4o.' },
              { icon: '✅', title: 'Smart Checklists', desc: 'Automated task assignments with deadlines, reminders, and progress tracking.' },
              { icon: '📄', title: 'Document Manager', desc: 'Upload, sign, and manage all HR documents in one secure place.' },
              { icon: '📊', title: 'Analytics Dashboard', desc: 'Real-time insights on completion rates, bottlenecks, and time-to-productivity.' },
              { icon: '🔔', title: 'Auto Notifications', desc: 'Email and Slack notifications keep everyone on track automatically.' },
              { icon: '🎯', title: 'Role Templates', desc: 'Pre-built templates for 50+ roles — Engineer, Sales, Marketing, Support.' },
            ].map(f => (
              <div key={f.title} className="p-6 bg-white/5 border border-white/10 rounded-2xl hover:border-purple-500/50 transition group">
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-lg font-bold mb-2 group-hover:text-purple-400 transition">{f.title}</h3>
                <p className="text-gray-400 text-sm">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="py-24 px-6 bg-white/5">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-4">How It Works</h2>
          <p className="text-center text-gray-400 mb-16">Get started in under 5 minutes</p>
          <div className="space-y-8">
            {[
              { step: '01', title: 'Add New Employee', desc: 'Enter employee name, role, start date and department.' },
              { step: '02', title: 'AI Generates Plan', desc: 'Our AI creates a full personalized onboarding plan instantly.' },
              { step: '03', title: 'Employee Gets Access', desc: 'Employee receives login and starts completing their onboarding tasks.' },
              { step: '04', title: 'Track & Optimize', desc: 'Monitor progress in real-time and get insights to improve.' },
            ].map(s => (
              <div key={s.step} className="flex gap-6 items-start">
                <div className="text-5xl font-extrabold text-purple-500/30 w-16 shrink-0">{s.step}</div>
                <div>
                  <h3 className="text-xl font-bold mb-1">{s.title}</h3>
                  <p className="text-gray-400">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-4">Simple Pricing</h2>
          <p className="text-center text-gray-400 mb-16">Start free. Scale as you grow.</p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { name: 'Starter', price: '$0', period: 'forever', features: ['Up to 3 employees/mo', 'Basic AI plans', 'Email support'], cta: 'Start Free', highlight: false },
              { name: 'Growth', price: '$99', period: '/month', features: ['Up to 25 employees/mo', 'Advanced AI plans', 'Slack integration', 'Analytics dashboard', 'Priority support'], cta: 'Start Trial', highlight: true },
              { name: 'Enterprise', price: '$499', period: '/month', features: ['Unlimited employees', 'Custom AI training', 'SSO & SAML', 'API access', 'Dedicated CSM'], cta: 'Contact Sales', highlight: false },
            ].map(p => (
              <div key={p.name} className={`p-8 rounded-2xl border ${p.highlight ? 'border-purple-500 bg-purple-500/10 scale-105' : 'border-white/10 bg-white/5'}`}>
                {p.highlight && <div className="text-xs font-bold text-purple-400 mb-3 uppercase tracking-wider">Most Popular</div>}
                <div className="text-xl font-bold mb-1">{p.name}</div>
                <div className="text-4xl font-extrabold mb-1">{p.price}<span className="text-lg text-gray-400 font-normal">{p.period}</span></div>
                <ul className="mt-6 space-y-3 mb-8">
                  {p.features.map(f => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-300"><span className="text-green-400">✓</span>{f}</li>
                  ))}
                </ul>
                <Link href="/register" className={`block text-center py-3 rounded-xl font-medium transition ${p.highlight ? 'bg-purple-600 hover:bg-purple-500' : 'border border-white/20 hover:border-white/40'}`}>{p.cta}</Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 text-center">
        <h2 className="text-4xl font-bold mb-4">Ready to Transform Onboarding?</h2>
        <p className="text-gray-400 mb-8">Join 500+ companies saving 40+ hours per new hire.</p>
        <Link href="/register" className="px-10 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 rounded-xl font-bold text-lg transition shadow-lg shadow-purple-500/25">
          Start Free Today →
        </Link>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/10 py-8 px-6 text-center text-gray-500 text-sm">
        <div className="flex items-center justify-center gap-2 mb-2">
          <span>🚀</span>
          <span className="font-bold text-white">OnboardAI</span>
        </div>
        <p>© 2026 OnboardAI. All rights reserved.</p>
      </footer>
    </main>
  );
}
