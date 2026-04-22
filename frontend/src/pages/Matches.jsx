import { useEffect, useState, useCallback } from 'react'
import { matchesApi } from '../services/api'
import MatchCard from '../components/MatchCard'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'

const TABS = ['upcoming', 'live', 'finished']

export default function Matches() {
  const [tab, setTab] = useState('upcoming')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [data, setData] = useState({ matches: [], total: 0 })
  const [loading, setLoading] = useState(false)

  const LIMIT = 12

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await matchesApi.list({ status: tab, search, limit: LIMIT, offset: page * LIMIT })
      setData(r.data)
    } finally {
      setLoading(false)
    }
  }, [tab, search, page])

  useEffect(() => { load() }, [load])
  useEffect(() => { setPage(0) }, [tab, search])

  const totalPages = Math.ceil(data.total / LIMIT)

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Matches</h1>

      {/* Tabs */}
      <div className="flex gap-2">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded-lg text-sm capitalize transition ${tab === t ? 'bg-green-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Search team or league..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-sm outline-none focus:border-green-500"
        />
      </div>

      {loading ? (
        <div className="text-slate-400 text-center py-10">Loading...</div>
      ) : data.matches.length === 0 ? (
        <div className="text-slate-400 text-center py-10 bg-slate-800 rounded-xl">No matches found.</div>
      ) : (
        <>
          <p className="text-xs text-slate-400">{data.total} match{data.total !== 1 ? 'es' : ''}</p>
          <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {data.matches.map(m => <MatchCard key={m.id} match={m} />)}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2">
              <button onClick={() => setPage(p => p - 1)} disabled={page === 0} className="p-1 disabled:opacity-30">
                <ChevronLeft size={18} />
              </button>
              <span className="text-sm text-slate-400">Page {page + 1} / {totalPages}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1} className="p-1 disabled:opacity-30">
                <ChevronRight size={18} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
