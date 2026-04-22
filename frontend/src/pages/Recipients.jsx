import { useEffect, useState } from 'react'
import { recipientsApi } from '../services/api'
import { Plus, Trash2, ToggleLeft, ToggleRight, Send, CheckCircle, XCircle } from 'lucide-react'

export default function Recipients() {
  const [recipients, setRecipients] = useState([])
  const [logs, setLogs] = useState([])
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name: '', phone_number: '' })
  const [error, setError] = useState('')
  const [testing, setTesting] = useState(null)
  const [tab, setTab] = useState('recipients')

  const load = async () => {
    const [r, l] = await Promise.all([recipientsApi.list(), recipientsApi.logs()])
    setRecipients(r.data)
    setLogs(l.data)
  }

  useEffect(() => { load() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await recipientsApi.add(form)
      setForm({ name: '', phone_number: '' })
      setShowAdd(false)
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to add recipient')
    }
  }

  const toggleActive = async (r) => {
    await recipientsApi.update(r.id, { active: !r.active })
    load()
  }

  const handleDelete = async (id) => {
    if (!confirm('Remove this recipient?')) return
    await recipientsApi.remove(id)
    load()
  }

  const handleTest = async (id) => {
    setTesting(id)
    try {
      await recipientsApi.test(id)
      alert('Test message sent!')
    } catch (e) {
      alert('Failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setTesting(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">WhatsApp Notifications</h1>
        <button
          onClick={() => setShowAdd(v => !v)}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg text-sm"
        >
          <Plus size={14} /> Add Recipient
        </button>
      </div>

      {/* Add form */}
      {showAdd && (
        <form onSubmit={handleAdd} className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-3">
          <h3 className="font-semibold">New Recipient</h3>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <input
            required
            placeholder="Name"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-500"
          />
          <input
            required
            placeholder="Phone number (e.g. +263785186616)"
            value={form.phone_number}
            onChange={e => setForm(f => ({ ...f, phone_number: e.target.value }))}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-500"
          />
          <div className="flex gap-2">
            <button type="submit" className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm">Add</button>
            <button type="button" onClick={() => setShowAdd(false)} className="bg-slate-700 text-slate-300 px-4 py-2 rounded-lg text-sm">Cancel</button>
          </div>
        </form>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        {['recipients', 'logs'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded-lg text-sm capitalize transition ${tab === t ? 'bg-green-600 text-white' : 'bg-slate-800 text-slate-400'}`}
          >
            {t === 'recipients' ? `Recipients (${recipients.length})` : `Send Logs (${logs.length})`}
          </button>
        ))}
      </div>

      {tab === 'recipients' ? (
        <div className="space-y-3">
          {recipients.length === 0 ? (
            <div className="text-slate-400 text-center py-10 bg-slate-800 rounded-xl">No recipients yet.</div>
          ) : recipients.map(r => (
            <div key={r.id} className="bg-slate-800 border border-slate-700 rounded-xl p-4 flex items-center gap-3">
              <div className="flex-1">
                <div className="font-semibold">{r.name}</div>
                <div className="text-sm text-slate-400">{r.phone_number}</div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => toggleActive(r)} title={r.active ? 'Deactivate' : 'Activate'} className={r.active ? 'text-green-400' : 'text-slate-500'}>
                  {r.active ? <ToggleRight size={22} /> : <ToggleLeft size={22} />}
                </button>
                <button
                  onClick={() => handleTest(r.id)}
                  disabled={testing === r.id}
                  title="Send test message"
                  className="text-blue-400 hover:text-blue-300 disabled:opacity-40"
                >
                  <Send size={16} />
                </button>
                <button onClick={() => handleDelete(r.id)} title="Remove" className="text-red-400 hover:text-red-300">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {logs.length === 0 ? (
            <div className="text-slate-400 text-center py-10 bg-slate-800 rounded-xl">No notifications sent yet.</div>
          ) : logs.map(l => (
            <div key={l.id} className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 flex items-center gap-3">
              {l.status === 'sent'
                ? <CheckCircle size={16} className="text-green-400 shrink-0" />
                : <XCircle size={16} className="text-red-400 shrink-0" />}
              <div className="flex-1 min-w-0">
                <div className="text-xs text-slate-400">{new Date(l.sent_at).toLocaleString()}</div>
                {l.error && <div className="text-xs text-red-400 truncate">{l.error}</div>}
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${l.status === 'sent' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                {l.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
