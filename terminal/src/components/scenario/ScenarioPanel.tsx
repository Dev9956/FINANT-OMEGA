// FININT OMEGA — Scenario Analysis — wired to real backend API

import { useState, useEffect, useCallback } from 'react'
import { BarChart3, RefreshCw, Loader2, Plus } from 'lucide-react'
import { scenarios } from '../../api/client'

interface Scenario {
  scenario_id: string
  title: string
  description: string
  variables: { name: string; current_value: number; scenario_value: number; unit: string }[]
  status: string
  created_at: string
}

export function ScenarioPanel() {
  const [scenarioList, setScenarioList] = useState<Scenario[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({
    title: 'Revenue Growth Scenario',
    description: 'What if revenue grows 25% instead of 15%?',
    variables: [
      { name: 'revenue_growth', current_value: 0.15, scenario_value: 0.25, unit: '%' },
      { name: 'margin', current_value: 0.45, scenario_value: 0.47, unit: '%' },
      { name: 'pe_ratio', current_value: 72, scenario_value: 65, unit: 'x' },
    ],
  })

  const fetchScenarios = useCallback(async () => {
    setLoading(true)
    try {
      const data = await scenarios.list() as any
      setScenarioList(data.scenarios || [])
    } catch {} finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchScenarios() }, [fetchScenarios])

  const selected = scenarioList.find(s => s.scenario_id === selectedId)

  const handleCreate = async () => {
    if (!form.title.trim()) return
    setCreating(true)
    try {
      const result = await scenarios.create({
        title: form.title,
        description: form.description,
        variables: form.variables,
      }) as any
      await fetchScenarios()
      if (result?.scenario_id) setSelectedId(result.scenario_id)
    } catch {} finally { setCreating(false) }
  }

  const addVariable = () => {
    setForm(f => ({
      ...f,
      variables: [...f.variables, { name: '', current_value: 0, scenario_value: 0, unit: '' }],
    }))
  }

  const updateVariable = (idx: number, field: string, value: any) => {
    setForm(f => ({
      ...f,
      variables: f.variables.map((v, i) => i === idx ? { ...v, [field]: value } : v),
    }))
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 size={14} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Scenario Lab</span>
          <div className="flex-1" />
          <button onClick={fetchScenarios} className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} />
          </button>
        </div>

        {/* Create form */}
        <div className="space-y-1">
          <div className="flex gap-1">
            <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="Scenario title" className="flex-1 h-6 px-1.5 text-[10px] rounded border outline-none"
              style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          </div>
          <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            placeholder="Description..." className="w-full h-8 px-1.5 py-1 text-[10px] rounded border outline-none resize-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />

          {/* Variables */}
          <div className="space-y-1">
            <div className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Variables</div>
            {form.variables.map((v, i) => (
              <div key={i} className="flex items-center gap-1">
                <input value={v.name} onChange={e => updateVariable(i, 'name', e.target.value)}
                  placeholder="Name" className="w-20 h-5 px-1 text-[9px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
                <input type="number" value={v.current_value} onChange={e => updateVariable(i, 'current_value', +e.target.value)}
                  placeholder="Current" className="w-14 h-5 px-1 text-[9px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
                <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>→</span>
                <input type="number" value={v.scenario_value} onChange={e => updateVariable(i, 'scenario_value', +e.target.value)}
                  placeholder="Scenario" className="w-14 h-5 px-1 text-[9px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
                <input value={v.unit} onChange={e => updateVariable(i, 'unit', e.target.value)}
                  placeholder="Unit" className="w-8 h-5 px-1 text-[9px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
              </div>
            ))}
            <button onClick={addVariable} className="text-[9px] px-1.5 py-0.5 rounded border"
              style={{ borderColor: 'var(--border-primary)', color: 'var(--text-muted)' }}>
              + Add Variable
            </button>
          </div>

          <button onClick={handleCreate} disabled={creating}
            className="w-full h-7 rounded text-[10px] font-medium flex items-center justify-center gap-1"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {creating ? <Loader2 size={10} className="animate-spin" /> : <Plus size={10} />}
            {creating ? 'Creating...' : 'Create Scenario'}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-2">
        {loading ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin mr-2" /> Loading...
          </div>
        ) : scenarioList.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <BarChart3 size={24} className="mb-2 opacity-30" />
            <div className="text-xs">No scenarios yet</div>
          </div>
        ) : (
          <div className="space-y-2">
            {/* List */}
            <div className="space-y-1">
              {scenarioList.map(s => (
                <button key={s.scenario_id} onClick={() => setSelectedId(s.scenario_id === selectedId ? null : s.scenario_id)}
                  className="w-full p-2 rounded border text-left"
                  style={{
                    borderColor: selectedId === s.scenario_id ? 'var(--accent-blue)' : 'var(--border-primary)',
                    background: selectedId === s.scenario_id ? 'var(--accent-blue)' + '08' : 'var(--bg-secondary)',
                  }}>
                  <div className="flex items-center gap-2">
                    <BarChart3 size={12} style={{ color: selectedId === s.scenario_id ? 'var(--accent-blue)' : 'var(--text-muted)' }} />
                    <div className="flex-1 min-w-0">
                      <div className="text-[10px] font-medium" style={{ color: 'var(--text-primary)' }}>{s.title}</div>
                      <div className="text-[9px]" style={{ color: 'var(--text-muted)' }}>{s.variables?.length || 0} variables · {s.status}</div>
                    </div>
                    <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                      {new Date(s.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </button>
              ))}
            </div>

            {/* Detail */}
            {selected && (
              <div className="p-2 rounded border space-y-2" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                <div className="text-[10px] font-medium" style={{ color: 'var(--text-primary)' }}>{selected.title}</div>
                {selected.description && (
                  <div className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>{selected.description}</div>
                )}
                {selected.variables?.length > 0 && (
                  <div>
                    <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--text-muted)' }}>Variables</div>
                    <div className="rounded border" style={{ borderColor: 'var(--border-primary)' }}>
                      <div className="grid grid-cols-4 text-[9px] font-medium px-2 py-1 border-b"
                        style={{ borderColor: 'var(--border-primary)', color: 'var(--text-muted)' }}>
                        <span>Variable</span><span>Current</span><span>Scenario</span><span>Change</span>
                      </div>
                      {selected.variables.map((v, i) => {
                        const change = v.current_value !== 0
                          ? ((v.scenario_value - v.current_value) / Math.abs(v.current_value) * 100).toFixed(1)
                          : 'N/A'
                        const changeNum = parseFloat(change)
                        return (
                          <div key={i} className="grid grid-cols-4 text-[10px] px-2 py-1 border-t"
                            style={{ borderColor: 'var(--border-primary)' }}>
                            <span style={{ color: 'var(--text-primary)' }}>{v.name}</span>
                            <span className="font-mono" style={{ color: 'var(--text-muted)' }}>{v.current_value}{v.unit}</span>
                            <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{v.scenario_value}{v.unit}</span>
                            <span className="font-mono" style={{ color: isNaN(changeNum) ? 'var(--text-muted)' : changeNum >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                              {isNaN(changeNum) ? change : `${changeNum >= 0 ? '+' : ''}${change}%`}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
