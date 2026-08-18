// FININT OMEGA — AI Debate — wired to real backend API

import { useState, useEffect, useCallback } from 'react'
import { Swords, RefreshCw, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { debate } from '../../api/client'

interface DebateResult {
  debate_id: string
  question: string
  bull_argument: any
  bear_argument: any
  base_argument: any
  verdict: any
  confidence: number
  created_at: string
}

function getArgText(arg: any): string {
  if (typeof arg === 'string') return arg
  if (arg?.thesis) return arg.thesis
  if (arg?.key_points?.length) return arg.key_points.join('\n')
  if (arg?.analysis) return arg.analysis
  return JSON.stringify(arg)
}

export function DebatePanel() {
  const [debates, setDebates] = useState<DebateResult[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [question, setQuestion] = useState('Is NVDA fairly valued at current levels?')

  const fetchDebates = useCallback(async () => {
    setLoading(true)
    try {
      // Try to list existing debates (may not be available)
    } catch {} finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchDebates() }, [fetchDebates])

  const selected = debates.find(d => d.debate_id === selectedId)

  const handleStart = async () => {
    if (!question.trim()) return
    setCreating(true)
    try {
      const result = await debate.start({
        question,
        context: {},
        evidence_items: [],
      }) as DebateResult
      setDebates(prev => [result, ...prev])
      setSelectedId(result.debate_id)
    } catch {} finally { setCreating(false) }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2 mb-2">
          <Swords size={14} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>AI Debate</span>
          <div className="flex-1" />
          <button onClick={fetchDebates} className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} />
          </button>
        </div>
        <div className="flex items-center gap-1">
          <input value={question} onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleStart()}
            placeholder="Debate question..." className="flex-1 h-7 px-1.5 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <button onClick={handleStart} disabled={creating}
            className="h-7 px-2 rounded text-[10px] font-medium flex items-center gap-1"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {creating ? <Loader2 size={10} className="animate-spin" /> : <Swords size={10} />}
            {creating ? 'Debating...' : 'Start Debate'}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-2">
        {loading ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin mr-2" /> Loading...
          </div>
        ) : selected ? (
          <div className="space-y-2">
            {/* Question */}
            <div className="p-2 rounded border" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
              <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--text-muted)' }}>Question</div>
              <div className="text-xs" style={{ color: 'var(--text-primary)' }}>{selected.question}</div>
            </div>

            {/* Bull argument */}
            <div className="p-2 rounded border" style={{ borderColor: 'var(--accent-green)' + '33', background: 'var(--accent-green)' + '08' }}>
              <div className="flex items-center gap-1 mb-1">
                <TrendingUp size={10} style={{ color: 'var(--accent-green)' }} />
                <span className="text-[9px] font-semibold uppercase" style={{ color: 'var(--accent-green)' }}>Bull Case</span>
              </div>
              <div className="text-[10px] leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                {getArgText(selected.bull_argument)}
              </div>
            </div>

            {/* Bear argument */}
            <div className="p-2 rounded border" style={{ borderColor: 'var(--accent-red)' + '33', background: 'var(--accent-red)' + '08' }}>
              <div className="flex items-center gap-1 mb-1">
                <TrendingDown size={10} style={{ color: 'var(--accent-red)' }} />
                <span className="text-[9px] font-semibold uppercase" style={{ color: 'var(--accent-red)' }}>Bear Case</span>
              </div>
              <div className="text-[10px] leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                {getArgText(selected.bear_argument)}
              </div>
            </div>

            {/* Base argument */}
            <div className="p-2 rounded border" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
              <div className="flex items-center gap-1 mb-1">
                <Minus size={10} style={{ color: 'var(--text-muted)' }} />
                <span className="text-[9px] font-semibold uppercase" style={{ color: 'var(--text-muted)' }}>Base Case</span>
              </div>
              <div className="text-[10px] leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                {getArgText(selected.base_argument)}
              </div>
            </div>

            {/* Verdict */}
            <div className="p-2 rounded border" style={{ borderColor: 'var(--accent-blue)' + '33', background: 'var(--accent-blue)' + '08' }}>
              <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--accent-blue)' }}>Verdict</div>
              <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                {getArgText(selected.verdict) || 'No verdict'}
              </div>
              <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                Confidence: {(selected.confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <Swords size={24} className="mb-2 opacity-30" />
            <div className="text-xs">Start a bull/bear debate</div>
            <div className="text-[10px] mt-1">Enter a question above and click Start Debate</div>
          </div>
        )}
      </div>
    </div>
  )
}
