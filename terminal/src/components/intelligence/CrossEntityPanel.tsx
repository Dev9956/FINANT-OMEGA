// FININT OMEGA — Cross-Entity Analysis — wired to real backend API

import { useState, useEffect, useCallback } from 'react'
import { Network, RefreshCw, Loader2, Search } from 'lucide-react'
import { crossEntity } from '../../api/client'

interface AnalysisResult {
  result_id: string
  entities: string[]
  analysis_type: string
  finding: string
  confidence: number
  created_at: string
}

export function CrossEntityPanel() {
  const [results, setResults] = useState<AnalysisResult[]>([])
  const [loading, setLoading] = useState(false)
  const [entityInput, setEntityInput] = useState('NVDA,AMD,INTC')
  const [analyzing, setAnalyzing] = useState(false)
  const [activeQuery, setActiveQuery] = useState<string | null>(null)

  const fetchResults = useCallback(async () => {
    setLoading(true)
    try {
      // Try predefined queries
      const weakening = await crossEntity.weakeningThesis() as any
      const strong = await crossEntity.strongCashflow() as any
      const highAnomaly = await crossEntity.highAnomaly() as any

      const all: AnalysisResult[] = []
      if (weakening?.entities) all.push(...weakening.entities.map((r: any) => ({ ...r, analysis_type: 'weakening_thesis' })))
      if (strong?.entities) all.push(...strong.entities.map((r: any) => ({ ...r, analysis_type: 'strong_cashflow_low_valuation' })))
      if (highAnomaly?.entities) all.push(...highAnomaly.entities.map((r: any) => ({ ...r, analysis_type: 'high_anomaly' })))
      setResults(all)
    } catch {} finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchResults() }, [fetchResults])

  const handleAnalyze = async () => {
    const symbols = entityInput.split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
    if (symbols.length < 2) return
    setAnalyzing(true)
    try {
      // Register entities
      for (const sym of symbols) {
        try { await crossEntity.addEntities({ symbol: sym, name: sym }) } catch {}
      }
      // Run analysis
      const result = await crossEntity.analyze({ entities: symbols, analysis_type: 'correlation' }) as any
      if (result?.result_id) {
        const detail = await crossEntity.getResult(result.result_id) as any
        setResults(prev => [{ ...detail, result_id: result.result_id, analysis_type: 'custom' }, ...prev])
      }
    } catch {} finally { setAnalyzing(false) }
  }

  const runPredefined = async (type: string) => {
    setActiveQuery(type)
    setLoading(true)
    try {
      let data: any
      if (type === 'weakening') data = await crossEntity.weakeningThesis()
      else if (type === 'strong') data = await crossEntity.strongCashflow()
      else if (type === 'anomaly') data = await crossEntity.highAnomaly()
      if (data?.entities) {
        setResults(data.entities.map((r: any) => ({ ...r, analysis_type: type })))
      }
    } catch {} finally { setLoading(false) }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2 mb-2">
          <Network size={14} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Cross-Entity Analysis</span>
          <div className="flex-1" />
          <button onClick={fetchResults} className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} />
          </button>
        </div>

        {/* Quick analysis */}
        <div className="flex items-center gap-1 mb-2">
          <input value={entityInput} onChange={e => setEntityInput(e.target.value)}
            placeholder="NVDA,AMD,INTC"
            className="flex-1 h-7 px-2 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <button onClick={handleAnalyze} disabled={analyzing}
            className="h-7 px-2 rounded text-[10px] font-medium flex items-center gap-1"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {analyzing ? <Loader2 size={10} className="animate-spin" /> : <Search size={10} />}
            Analyze
          </button>
        </div>

        {/* Predefined queries */}
        <div className="flex gap-1">
          {[
            { key: 'weakening', label: 'Weakening Thesis' },
            { key: 'strong', label: 'Strong Cashflow' },
            { key: 'anomaly', label: 'High Anomaly' },
          ].map(q => (
            <button key={q.key} onClick={() => runPredefined(q.key)}
              className="text-[9px] px-1.5 py-0.5 rounded border"
              style={{
                borderColor: activeQuery === q.key ? 'var(--accent-blue)' : 'var(--border-primary)',
                color: activeQuery === q.key ? 'var(--accent-blue)' : 'var(--text-muted)',
              }}>
              {q.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-auto p-2 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin mr-2" /> Loading...
          </div>
        ) : results.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <Network size={24} className="mb-2 opacity-30" />
            <div className="text-xs">No analysis results yet</div>
            <div className="text-[10px] mt-1">Enter symbols above or run a predefined query</div>
          </div>
        ) : (
          results.map((r, i) => (
            <div key={r.result_id || i} className="p-2 rounded border"
              style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[9px] px-1.5 py-0.5 rounded"
                  style={{ background: 'var(--accent-blue)' + '15', color: 'var(--accent-blue)' }}>
                  {r.analysis_type?.replace(/_/g, ' ')}
                </span>
                {r.entities && (
                  <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                    {Array.isArray(r.entities) ? r.entities.join(', ') : r.entities}
                  </span>
                )}
              </div>
              <div className="text-xs" style={{ color: 'var(--text-primary)' }}>
                {r.finding || (r as any).description || 'No finding'}
              </div>
              {r.confidence > 0 && (
                <div className="mt-1 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                  Confidence: {(r.confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
