export default function ProbabilityBar({ home, draw, away, homeTeam, awayTeam }) {
  const h = Math.round((home || 0) * 100)
  const d = Math.round((draw || 0) * 100)
  const a = Math.round((away || 0) * 100)

  return (
    <div>
      <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
        <div className="bg-green-500" style={{ width: `${h}%` }} title={`Home: ${h}%`} />
        <div className="bg-slate-500" style={{ width: `${d}%` }} title={`Draw: ${d}%`} />
        <div className="bg-blue-500" style={{ width: `${a}%` }} title={`Away: ${a}%`} />
      </div>
      <div className="flex justify-between text-xs text-slate-400 mt-1">
        <span className="text-green-400">{homeTeam} {h}%</span>
        <span>Draw {d}%</span>
        <span className="text-blue-400">{a}% {awayTeam}</span>
      </div>
    </div>
  )
}
