import { Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, CalendarDays, TrendingUp, MessageCircle, RefreshCw } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Matches from './pages/Matches'
import Predictions from './pages/Predictions'
import Recipients from './pages/Recipients'
import { predictionsApi } from './services/api'
import { useState } from 'react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/matches', icon: CalendarDays, label: 'Matches' },
  { to: '/predictions', icon: TrendingUp, label: 'Predictions' },
  { to: '/recipients', icon: MessageCircle, label: 'WhatsApp' },
]

export default function App() {
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await predictionsApi.refresh()
      setTimeout(() => window.location.reload(), 2000)
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <header className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">⚽</span>
          <span className="text-xl font-bold text-green-400">AutoBet</span>
          <span className="text-slate-400 text-sm hidden sm:block">Football Intelligence</span>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-sm transition"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          {refreshing ? 'Syncing...' : 'Sync Odds'}
        </button>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <nav className="w-56 bg-slate-900 border-r border-slate-700 p-4 hidden md:block">
          <ul className="space-y-1">
            {navItems.map(({ to, icon: Icon, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
                      isActive
                        ? 'bg-green-600 text-white font-medium'
                        : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                    }`
                  }
                >
                  <Icon size={16} />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {/* Mobile bottom nav */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-700 flex z-50">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center py-2 text-xs transition ${
                  isActive ? 'text-green-400' : 'text-slate-400'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-4 sm:p-6 pb-20 md:pb-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/matches" element={<Matches />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/recipients" element={<Recipients />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
