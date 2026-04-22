export default function ConfidenceBadge({ value }) {
  const color =
    value >= 75 ? 'bg-green-600' :
    value >= 60 ? 'bg-yellow-600' :
    'bg-slate-600'

  return (
    <span className={`${color} text-white text-xs font-semibold px-2 py-0.5 rounded-full`}>
      {value?.toFixed(1)}%
    </span>
  )
}
