// FININT OMEGA — Thesis Studio — wired to real backend API

import { useState, useEffect, useCallback } from 'react'
import { Target, TrendingUp, RefreshCw, Zap, Plus, Loader2 } from 'lucide-react'
import { thesis as thesisApi } from '../../api/client'

interface ThesisData {
  thesis_id: string
  symbol: string
  title: string
  bull_case: string
  base_case: string
  bear_case: string
  key_drivers: string[]
  key_risks: string[]
  assumptions: string[]
  confidence: number
  time_horizon: string
  created_at: string
  updated_at: string
}

interface ThesisVersion {
  version_number: number
  thesis_id: string
  title: string
  confidence: number
  created_at: string
  change_reason: string
}

interface ThesisHistory {
  thesis_id: string
  versions: ThesisVersion[]
}

const confidenceColor = (c: number) => {
  if (c >= 0.7) return 'var(--accent-green)'
  if (c >= 0.5) return 'var(--accent-yellow)'
  return 'var(--accent-red)'
}

export function ThesisPanel() {
  const [theses, setTheses] = useState<ThesisData[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [history, setHistory] = useState<ThesisHistory | null>(null)
  const [loading, setLoading] = useState(true)
  const [evaluating, setEvaluating] = useState(false)
  const [creating, setCreating] = useState(false)
  const [activeTab, setActiveTab] = useState<'thesis' | 'versions'>('thesis')
  const [newSymbol, setNewSymbol] = useState('NVDA')
  const [newTitle, setNewTitle] = useState('AI Infrastructure Dominance')
  const [newBullCase, setNewBullCase] = useState('')
  const [evalResult, setEvalResult] = useState<any>(null)

  const fetchTheses = useCallback(async (symbol?: string) => {
    setLoading(true)
    try {
      const data = await thesisApi.list(symbol) as any
      setTheses(data.theses || [])
      if (data.theses?.length > 0 && !selectedId) {
        setSelectedId(data.theses[0].thesis_id)
      }
    } catch {} finally {
      setLoading(false)
    }
  }, [selectedId])

  const fetchHistory = useCallback(async (id: string) => {
    try {
      const data = await thesisApi.getHistory(id) as ThesisHistory
      setHistory(data)
    } catch {} finally {}
  }, [])

  useEffect(() => {
    fetchTheses()
  }, [])

  useEffect(() => {
    if (selectedId) fetchHistory(selectedId)
  }, [selectedId, fetchHistory])

  const selected = theses.find(t => t.thesis_id === selectedId)

  const handleCreate = async () => {
    if (!newSymbol.trim() || !newTitle.trim()) return
    setCreating(true)
    try {
      const result = await thesisApi.create({
        symbol: newSymbol.toUpperCase(),
        title: newTitle,
        bull_case: newBullCase,
        confidence: 0.7,
      }) as any
      await fetchTheses()
      setSelectedId(result.thesis_id)
    } catch {} finally {
      setCreating(false)
    }
  }

  const handleEvaluate = async () => {
    if (!selectedId) return
    setEvaluating(true)
    setEvalResult(null)
    try {
      const result = await thesisApi.evaluate(selectedId) as any
      setEvalResult(result)
      await fetchTheses()
      await fetchHistory(selectedId)
    } catch {} finally {
      setEvaluating(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Tabs */}
      <div className="flex items-center border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex">
          {[
            { key: 'thesis', label: 'Thesis' },
            { key: 'versions', label: `History (${history?.versions?.length || 0})` },
          ].map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key as any)}
              className="px-3 py-1.5 text-[10px] font-medium border-b-2 transition-colors"
              style={{
                borderColor: activeTab === tab.key ? 'var(--accent-blue)' : 'transparent',
                color: activeTab === tab.key ? 'var(--accent-blue)' : 'var(--text-muted)',
              }}>
              {tab.label}
            </button>
          ))}
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-1 pr-2">
          <button onClick={() => fetchTheses()} className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-3">
        {loading ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin mr-2" /> Loading theses...
          </div>
        ) : theses.length === 0 ? (
          /* No theses — create form */
          <div className="space-y-3">
            <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Create Your First Thesis</div>
            <div>
              <label className="text-[10px] uppercase" style={{ color: 'var(--text-muted)' }}>Symbol</label>
              <input value={newSymbol} onChange={e => setNewSymbol(e.target.value)}
                className="w-full h-7 px-2 text-xs rounded border outline-none mt-0.5"
                style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="text-[10px] uppercase" style={{ color: 'var(--text-muted)' }}>Title</label>
              <input value={newTitle} onChange={e => setNewTitle(e.target.value)}
                className="w-full h-7 px-2 text-xs rounded border outline-none mt-0.5"
                style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="text-[10px] uppercase" style={{ color: 'var(--text-muted)' }}>Bull Case</label>
              <textarea value={newBullCase} onChange={e => setNewBullCase(e.target.value)}
                className="w-full h-16 px-2 py-1 text-xs rounded border outline-none mt-0.5 resize-none"
                style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
            </div>
            <button onClick={handleCreate} disabled={creating}
              className="h-8 px-3 rounded text-xs font-medium flex items-center gap-1"
              style={{ background: 'var(--accent-blue)', color: 'white' }}>
              {creating ? <Loader2 size={12} className="animate-spin" /> : <Plus size={12} />}
              {creating ? 'Creating...' : 'Create Thesis'}
            </button>
          </div>
        ) : activeTab === 'thesis' && selected ? (
          <div className="space-y-3">
            {/* Header */}
            <div className="flex items-start gap-2">
              <TrendingUp size={14} style={{ color: 'var(--accent-green)' }} />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{selected.symbol}</span>
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{selected.title}</span>
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <div className="flex items-center gap-1">
                    <Target size={10} style={{ color: confidenceColor(selected.confidence) }} />
                    <span className="text-[10px] font-mono" style={{ color: confidenceColor(selected.confidence) }}>
                      {(selected.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  {selected.time_horizon && (
                    <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                      {selected.time_horizon}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Cases */}
            {selected.bull_case && (
              <div className="p-2 rounded border" style={{ borderColor: 'var(--accent-green)' + '33', background: 'var(--accent-green)' + '08' }}>
                <div className="text-[10px] uppercase mb-1" style={{ color: 'var(--accent-green)' }}>Bull Case</div>
                <div className="text-xs leading-relaxed" style={{ color: 'var(--text-primary)' }}>{selected.bull_case}</div>
              </div>
            )}
            {selected.base_case && (
              <div className="p-2 rounded border" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                <div className="text-[10px] uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Base Case</div>
                <div className="text-xs leading-relaxed" style={{ color: 'var(--text-primary)' }}>{selected.base_case}</div>
              </div>
            )}
            {selected.bear_case && (
              <div className="p-2 rounded border" style={{ borderColor: 'var(--accent-red)' + '33', background: 'var(--accent-red)' + '08' }}>
                <div className="text-[10px] uppercase mb-1" style={{ color: 'var(--accent-red)' }}>Bear Case</div>
                <div className="text-xs leading-relaxed" style={{ color: 'var(--text-primary)' }}>{selected.bear_case}</div>
              </div>
            )}

            {/* Key drivers */}
            {selected.key_drivers?.length > 0 && (
              <div>
                <div className="text-[10px] uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Key Drivers</div>
                <div className="flex flex-wrap gap-1">
                  {selected.key_drivers.map((d, i) => (
                    <span key={i} className="text-[10px] px-1.5 py-0.5 rounded"
                      style={{ background: 'var(--accent-blue)' + '15', color: 'var(--accent-blue)' }}>
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Confidence bar */}
            <div>
              <div className="flex justify-between text-[10px] mb-1">
                <span style={{ color: 'var(--text-muted)' }}>Confidence</span>
                <span style={{ color: confidenceColor(selected.confidence) }}>{(selected.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                <div className="h-full rounded-full transition-all" style={{
                  width: `${selected.confidence * 100}%`,
                  background: confidenceColor(selected.confidence),
                }} />
              </div>
            </div>

            {/* Eval result */}
            {evalResult && (
              <div className="p-2 rounded border text-[10px]"
                style={{ borderColor: 'var(--accent-green)', background: 'var(--accent-green)' + '08' }}>
                <div className="font-medium mb-1" style={{ color: 'var(--accent-green)' }}>Evaluation Complete</div>
                <div style={{ color: 'var(--text-secondary)' }}>
                  Confidence: {evalResult.new_confidence !== undefined ? (evalResult.new_confidence * 100).toFixed(0) + '%' : 'N/A'}
                </div>
                {evalResult.evaluation_summary && (
                  <div className="mt-1" style={{ color: 'var(--text-muted)' }}>{evalResult.evaluation_summary}</div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-1">
              <button onClick={handleEvaluate} disabled={evaluating}
                className="flex-1 h-7 rounded text-[10px] font-medium flex items-center justify-center gap-1"
                style={{ background: 'var(--accent-green)', color: 'white' }}>
                {evaluating ? <Loader2 size={10} className="animate-spin" /> : <Zap size={10} />}
                {evaluating ? 'Evaluating...' : 'Evaluate Thesis'}
              </button>
              <button onClick={() => fetchTheses()}
                className="h-7 px-3 rounded text-[10px] font-medium border flex items-center gap-1"
                style={{ borderColor: 'var(--border-primary)', color: 'var(--text-secondary)' }}>
                <RefreshCw size={10} /> Refresh
              </button>
            </div>
          </div>
        ) : activeTab === 'versions' && history ? (
          <div className="space-y-1">
            {[...history.versions].reverse().map((v, i) => (
              <div key={v.version_number} className="flex items-start gap-2 px-2 py-1.5 rounded border"
                style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                <div className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0"
                  style={{ background: i === 0 ? 'var(--accent-blue)' : 'var(--bg-tertiary)', color: i === 0 ? 'white' : 'var(--text-muted)' }}>
                  v{v.version_number}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[10px]" style={{ color: 'var(--text-primary)' }}>{v.title}</div>
                  <div className="flex gap-2 mt-0.5">
                    <span className="text-[9px] font-mono" style={{ color: confidenceColor(v.confidence) }}>
                      {(v.confidence * 100).toFixed(0)}%
                    </span>
                    <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>{v.change_reason}</span>
                  </div>
                </div>
                <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                  {new Date(v.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-center py-8" style={{ color: 'var(--text-muted)' }}>
            Select a thesis or create a new one
          </div>
        )}
      </div>
    </div>
  )
}
