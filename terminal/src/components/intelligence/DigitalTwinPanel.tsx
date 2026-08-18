// FININT OMEGA — Digital Twin — wired to real backend API

import { useState, useEffect, useCallback } from 'react'
import { Cpu, RefreshCw, Loader2, Plus, Play } from 'lucide-react'
import { digitalTwin } from '../../api/client'

interface Twin {
  twin_id: string
  entity: string
  name: string
  description: string
  financials: Record<string, number>
  market: Record<string, number>
  valuation: Record<string, number>
  risk: Record<string, number>
  created_at: string
  updated_at: string
}

export function DigitalTwinPanel() {
  const [twins, setTwins] = useState<Twin[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [simulating, setSimulating] = useState(false)
  const [form, setForm] = useState({ entity: 'NVDA', name: 'NVIDIA Digital Twin', description: '' })
  const [scenarioForm, setScenarioForm] = useState('Revenue +20%')

  const fetchTwins = useCallback(async () => {
    setLoading(true)
    try {
      const data = await digitalTwin.list() as any
      setTwins(data.twins || [])
    } catch {} finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchTwins() }, [fetchTwins])

  const selected = twins.find(t => t.twin_id === selectedId)

  const handleCreate = async () => {
    if (!form.entity.trim()) return
    setCreating(true)
    try {
      const result = await digitalTwin.create({
        entity: form.entity.toUpperCase(),
        name: form.name,
        description: form.description,
      }) as any
      await fetchTwins()
      if (result?.twin_id) setSelectedId(result.twin_id)
    } catch {} finally { setCreating(false) }
  }

  const handleSimulate = async () => {
    if (!selectedId || !scenarioForm.trim()) return
    setSimulating(true)
    try {
      await digitalTwin.scenario(selectedId, { scenario: scenarioForm })
      await fetchTwins()
    } catch {} finally { setSimulating(false) }
  }

  const handleSnapshot = async () => {
    if (!selectedId) return
    setSimulating(true)
    try {
      await digitalTwin.snapshot(selectedId)
      await fetchTwins()
    } catch {} finally { setSimulating(false) }
  }

  const formatMetrics = (obj: Record<string, number>) => {
    if (!obj || Object.keys(obj).length === 0) return null
    return Object.entries(obj).map(([k, v]) => (
      <div key={k} className="flex justify-between text-[10px]">
        <span style={{ color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}</span>
        <span className="font-mono" style={{ color: 'var(--text-primary)' }}>
          {typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : v}
        </span>
      </div>
    ))
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2 mb-2">
          <Cpu size={14} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Digital Twin</span>
          <div className="flex-1" />
          <button onClick={fetchTwins} className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} />
          </button>
        </div>

        {/* Create form */}
        <div className="flex items-center gap-1">
          <input value={form.entity} onChange={e => setForm(f => ({ ...f, entity: e.target.value }))}
            placeholder="Symbol" className="w-16 h-7 px-1.5 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            placeholder="Twin name" className="flex-1 h-7 px-1.5 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <button onClick={handleCreate} disabled={creating}
            className="h-7 px-2 rounded text-[10px] font-medium flex items-center gap-1"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {creating ? <Loader2 size={8} className="animate-spin" /> : <Plus size={8} />}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin mr-2" /> Loading...
          </div>
        ) : twins.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <Cpu size={24} className="mb-2 opacity-30" />
            <div className="text-xs">No digital twins yet</div>
            <div className="text-[10px] mt-1">Create one above to start simulation</div>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {/* Twin list */}
            <div className="space-y-1">
              {twins.map(t => (
                <button key={t.twin_id} onClick={() => setSelectedId(t.twin_id === selectedId ? null : t.twin_id)}
                  className="w-full p-2 rounded border text-left flex items-center gap-2"
                  style={{
                    borderColor: selectedId === t.twin_id ? 'var(--accent-blue)' : 'var(--border-primary)',
                    background: selectedId === t.twin_id ? 'var(--accent-blue)' + '08' : 'var(--bg-secondary)',
                  }}>
                  <Cpu size={12} style={{ color: selectedId === t.twin_id ? 'var(--accent-blue)' : 'var(--text-muted)' }} />
                  <div className="flex-1 min-w-0">
                    <div className="text-[10px] font-medium" style={{ color: 'var(--text-primary)' }}>{t.name}</div>
                    <div className="text-[9px]" style={{ color: 'var(--text-muted)' }}>{t.entity}</div>
                  </div>
                  <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                    {new Date(t.updated_at).toLocaleDateString()}
                  </span>
                </button>
              ))}
            </div>

            {/* Selected twin detail */}
            {selected && (
              <div className="p-2 rounded border space-y-2" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                <div className="text-[10px] font-medium" style={{ color: 'var(--text-primary)' }}>
                  {selected.name} ({selected.entity})
                </div>

                {/* Metrics sections */}
                {[
                  { label: 'Financials', data: selected.financials },
                  { label: 'Market', data: selected.market },
                  { label: 'Valuation', data: selected.valuation },
                  { label: 'Risk', data: selected.risk },
                ].map(section => section.data && Object.keys(section.data).length > 0 && (
                  <div key={section.label}>
                    <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--text-muted)' }}>{section.label}</div>
                    <div className="p-1.5 rounded" style={{ background: 'var(--bg-primary)' }}>
                      {formatMetrics(section.data)}
                    </div>
                  </div>
                ))}

                {/* Scenario simulation */}
                <div className="flex items-center gap-1">
                  <input value={scenarioForm} onChange={e => setScenarioForm(e.target.value)}
                    placeholder="Scenario: Revenue +20%"
                    className="flex-1 h-7 px-1.5 text-[10px] rounded border outline-none"
                    style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
                  <button onClick={handleSimulate} disabled={simulating}
                    className="h-7 px-2 rounded text-[10px] font-medium flex items-center gap-1"
                    style={{ background: 'var(--accent-green)', color: 'white' }}>
                    {simulating ? <Loader2 size={8} className="animate-spin" /> : <Play size={8} />}
                    Simulate
                  </button>
                  <button onClick={handleSnapshot} disabled={simulating}
                    className="h-7 px-2 rounded text-[10px] font-medium border"
                    style={{ borderColor: 'var(--border-primary)', color: 'var(--text-secondary)' }}>
                    Snapshot
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
