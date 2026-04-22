import { format, parseISO } from 'date-fns'
import ConfidenceBadge from './ConfidenceBadge'
import ProbabilityBar from './ProbabilityBar'
import { Trophy, Flame } from 'lucide-react'
import clsx from 'clsx'

const outcomeLabel = { home_win: 'Home Win', draw: 'Draw', away_win: 'Away Win' }
const outcomeColor = { home_win: 'text-green-400', draw: 'text-slate-300', away_win: 'text-blue-400' }

export default function MatchCard({ match }) {
  const { prediction, odds } = match
  const matchDate = parseISO(match.match_date)

  return (
    <div className={clsx(
      'bg-slate-800 rounded-xl p-4 border transition',
      prediction?.value_bet ? 'border-yellow-500' : 'border-slate-700 hover:border-slate-600'
    )}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Trophy size={12} />
            <span>{match.league}</span>
            <span>·</span>
            <span>{format(matchDate, 'dd MMM HH:mm')}</span>
          </div>
          <div className="text-base font-semibold">
            {match.home_team} <span className="text-slate-400 font-normal mx-1">vs</span> {match.away_team}
          </div>
        </div>
        {prediction?.value_bet && (
          <span className="flex items-center gap-1 text-yellow-400 text-xs font-bold bg-yellow-400/10 px-2 py-1 rounded-full">
            <Flame size={12} /> VALUE
          </span>
        )}
      </div>

      {/* Odds row */}
      {odds && (
        <div className="grid grid-cols-3 gap-2 mb-3">
          {[
            { label: '1', value: odds.home_win },
            { label: 'X', value: odds.draw },
            { label: '2', value: odds.away_win },
          ].map(({ label, value }) => (
            <div key={label} className="bg-slate-900 rounded-lg text-center py-1.5">
              <div className="text-xs text-slate-400">{label}</div>
              <div className="font-bold text-white">{value?.toFixed(2) ?? '—'}</div>
            </div>
          ))}
        </div>
      )}

      {/* Prediction */}
      {prediction && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className={`font-semibold ${outcomeColor[prediction.predicted_outcome]}`}>
              {outcomeLabel[prediction.predicted_outcome]}
            </span>
            <ConfidenceBadge value={prediction.confidence} />
          </div>

          <ProbabilityBar
            home={prediction.home_win_prob}
            draw={prediction.draw_prob}
            away={prediction.away_win_prob}
            homeTeam={match.home_team}
            awayTeam={match.away_team}
          />

          {/* Secondary markets */}
          <div className="flex flex-wrap gap-2 mt-1">
            {prediction.predicted_goals && (
              <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">
                ⚽ {prediction.predicted_goals.replace('_', ' ')} {prediction.goals_confidence?.toFixed(0)}%
              </span>
            )}
            {prediction.btts_prediction && (
              <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">
                🔄 BTTS {prediction.btts_prediction.toUpperCase()} {prediction.btts_confidence?.toFixed(0)}%
              </span>
            )}
            {prediction.best_odds && (
              <span className="text-xs bg-slate-700 px-2 py-0.5 rounded">
                💰 {prediction.best_odds} @ {prediction.best_bookmaker}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
