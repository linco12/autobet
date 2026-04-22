import { useEffect, useState } from 'react'
import { predictionsApi, adminApi, matchesApi } from '../services/api'
import MatchCard from '../components/MatchCard'
import { TrendingUp, Flame, Target, Send, RefreshCw } from 'lucide-react'
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [topPredictions, setTopPredictions] = useState([])
  const [todayMatches, setTodayMatches] = useState([])
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState(null)

  useEffect(() => {
    predictionsApi.stats().then(r => setStats(r.data))
    predictionsApi.top({ limit: 6 }).then(r => setTopPredictions(r.data))
    matchesApi.today().then(r => setTodayMatches(r.data))
  }, [])

  const handleSendNow = async () => {
    setSending(true)
    setSendResult(null)
    try {
      const r = await adminApi.sendNow()
      setSendResult(r.data)
    } catch (e) {
      setSendResult({ error: e.message })
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          onClick={handleSendNow}
          disabled={sending}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm"
        >
          <Send size={14} className={sending ? 'animate-pulse' : ''} />
          {sending ? 'Sending...' : 'Send WhatsApp Now'}
        </button>
      </div>

      {sendResult && (
        <div className={`rounded-lg px-4 py-2 text-sm ${sendResult.error ? 'bg-red-900/50 text-red-300' : 'bg-green-900/50 text-green-300'}`}>
          {sendResult.error ? `Error: ${sendResult.error}` : `Sent: ${sendResult.sent} | Failed: ${sendResult.failed}`}
        </div>
      )}

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard icon={<TrendingUp size={20} />} label="Total Predictions" value={stats.total_predictions} color="text-blue-400" />
          <StatCard icon={<Flame size={20} />} label="Value Bets" value={stats.value_bets} color="text-yellow-400" />
          <StatCard icon={<Target size={20} />} label="High Confidence" value={stats.high_confidence} color="text-green-400" />
          <StatCard icon={<RefreshCw size={20} />} label="Today's Matches" value={todayMatches.length} color="text-purple-400" />
        </div>
      )}

      {/* Top predictions */}
      <section>
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Flame size={18} className="text-yellow-400" /> Top Picks Today
        </h2>
        {topPredictions.length === 0 ? (
          <EmptyState message="No predictions yet. Click Sync Odds to fetch data." />
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {topPredictions.map((p) => (
              <div key={p.match_id} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                <div className="text-xs text-slate-400 mb-1">{p.league}</div>
                <div className="font-semibold mb-2">{p.home_team} vs {p.away_team}</div>
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${p.predicted_outcome === 'home_win' ? 'text-green-400' : p.predicted_outcome === 'away_win' ? 'text-blue-400' : 'text-slate-300'}`}>
                    {p.predicted_outcome?.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${p.confidence >= 75 ? 'bg-green-600' : p.confidence >= 60 ? 'bg-yellow-600' : 'bg-slate-600'} text-white`}>
                    {p.confidence?.toFixed(1)}%
                  </span>
                </div>
                {p.value_bet && (
                  <div className="mt-2 text-xs text-yellow-400 font-bold">🔥 VALUE BET — {p.best_odds} odds</div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Today's matches */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Today's Matches</h2>
        {todayMatches.length === 0 ? (
          <EmptyState message="No matches scheduled today yet." />
        ) : (
          <div className="grid sm:grid-cols-2 gap-4">
            {todayMatches.map(m => <MatchCard key={m.id} match={m} />)}
          </div>
        )}
      </section>
    </div>
  )
}

function StatCard({ icon, label, value, color }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className={`${color} mb-2`}>{icon}</div>
      <div className="text-2xl font-bold">{value ?? '—'}</div>
      <div className="text-xs text-slate-400 mt-0.5">{label}</div>
    </div>
  )
}

function EmptyState({ message }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center text-slate-400">
      {message}
    </div>
  )
}
