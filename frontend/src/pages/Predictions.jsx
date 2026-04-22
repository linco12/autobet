import { useEffect, useState } from 'react'
import { predictionsApi } from '../services/api'
import ConfidenceBadge from '../components/ConfidenceBadge'
import { Flame, Filter } from 'lucide-react'

const outcomeLabel = { home_win: 'Home Win', draw: 'Draw', away_win: 'Away Win' }
const outcomeColor = { home_win: 'text-green-400', draw: 'text-slate-300', away_win: 'text-blue-400' }

export default function Predictions() {
  const [preds, setPreds] = useState([])
  const [valueOnly, setValueOnly] = useState(false)
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await predictionsApi.top({ limit: 30, value_only: valueOnly })
      setPreds(r.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [valueOnly])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Predictions</h1>
        <button
          onClick={() => setValueOnly(v => !v)}
          className={`flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg transition ${valueOnly ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}
        >
          <Filter size={14} /> {valueOnly ? 'Value Bets Only' : 'All Predictions'}
        </button>
      </div>

      {loading ? (
        <div className="text-slate-400 text-center py-10">Loading...</div>
      ) : preds.length === 0 ? (
        <div className="text-slate-400 text-center py-10 bg-slate-800 rounded-xl">No predictions available. Try syncing odds.</div>
      ) : (
        <div className="space-y-3">
          {preds.map(p => (
            <div key={p.match_id}>
              <div
                onClick={() => setSelected(selected?.match_id === p.match_id ? null : p)}
                className={`bg-slate-800 border rounded-xl p-4 cursor-pointer transition ${p.value_bet ? 'border-yellow-500/60' : 'border-slate-700 hover:border-slate-600'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="text-xs text-slate-400 mb-1">{p.league} · {p.match_date}</div>
                    <div className="font-semibold">{p.home_team} vs {p.away_team}</div>
                  </div>
                  <div className="flex flex-col items-end gap-1 ml-3">
                    <ConfidenceBadge value={p.confidence} />
                    {p.value_bet && (
                      <span className="text-yellow-400 text-xs font-bold flex items-center gap-1">
                        <Flame size={11} /> VALUE
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-2 flex items-center gap-4">
                  <span className={`text-sm font-medium ${outcomeColor[p.predicted_outcome]}`}>
                    {outcomeLabel[p.predicted_outcome]}
                  </span>
                  {p.best_odds && (
                    <span className="text-xs text-slate-400">@ {p.best_odds} ({p.best_bookmaker})</span>
                  )}
                </div>

                <div className="flex gap-2 mt-2 flex-wrap">
                  {p.predicted_goals && (
                    <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">
                      ⚽ {p.predicted_goals.replace('_', ' ')} {p.goals_confidence?.toFixed(0)}%
                    </span>
                  )}
                  {p.btts_prediction && (
                    <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">
                      🔄 BTTS {p.btts_prediction.toUpperCase()} {p.btts_confidence?.toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>

              {/* Expanded analysis */}
              {selected?.match_id === p.match_id && (
                <ReasoningPanel matchId={p.match_id} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ReasoningPanel({ matchId }) {
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    predictionsApi.get(matchId).then(r => setDetail(r.data))
  }, [matchId])

  if (!detail) return <div className="bg-slate-900 rounded-b-xl p-4 text-slate-400 text-sm">Loading analysis...</div>

  return (
    <div className="bg-slate-900 border border-t-0 border-slate-700 rounded-b-xl p-4 space-y-3">
      <h3 className="font-semibold text-sm text-green-400">Analysis & Reasoning</h3>
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Home Win', prob: detail.home_win_prob },
          { label: 'Draw', prob: detail.draw_prob },
          { label: 'Away Win', prob: detail.away_win_prob },
        ].map(({ label, prob }) => (
          <div key={label} className="bg-slate-800 rounded-lg p-2 text-center">
            <div className="text-xs text-slate-400">{label}</div>
            <div className="font-bold text-lg">{Math.round(prob * 100)}%</div>
          </div>
        ))}
      </div>
      {detail.reasoning && (
        <pre className="text-xs text-slate-300 whitespace-pre-wrap font-sans bg-slate-800 rounded-lg p-3">
          {detail.reasoning}
        </pre>
      )}
    </div>
  )
}
