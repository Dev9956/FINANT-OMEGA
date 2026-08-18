// FININT OMEGA — Investment Memo — wired to real backend API

import { useState, useEffect, useCallback } from 'react'
import { FileText, Loader2, Download, RefreshCw, Plus } from 'lucide-react'
import { memo as memoApi } from '../../api/client'

interface Memo {
  memo_id: string
  entity: string
  title: string
  thesis?: any
  bull_case?: any
  base_case?: any
  bear_case?: any
  key_risks?: string[]
  key_drivers?: string[]
  recommendation?: string
  confidence: number
  created_at: string
  executive_summary?: any
}

function getSectionContent(section: any): string {
  if (typeof section === 'string') return section
  if (section?.content) return section.content
  return ''
}

export function MemoPanel() {
  const [memos, setMemos] = useState<Memo[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [rendering, setRendering] = useState(false)
  const [rendered, setRendered] = useState<string | null>(null)
  const [form, setForm] = useState({
    entity: 'NVDA',
    thesis: 'AI Infrastructure Dominance',
    bull_case: 'NVIDIA maintains >80% AI GPU market share through 2026',
    base_case: 'Revenue growth decelerates to 30% YoY as competition increases',
    bear_case: 'AMD MI300 captures 15% market share, margin compression',
  })

  const fetchMemos = useCallback(async () => {
    try {
      // List memos - try with entity filter
      const data = await memoApi.get('list') as any
      if (data?.memos) setMemos(data.memos)
    } catch {
      // Memo list may not be available, create only
    }
  }, [])

  useEffect(() => { fetchMemos() }, [fetchMemos])

  const selected = memos.find(m => m.memo_id === selectedId)

  const handleGenerate = async () => {
    if (!form.entity.trim()) return
    setGenerating(true)
    try {
      const result = await memoApi.generate({
        entity: form.entity.toUpperCase(),
        thesis: form.thesis,
        bull_case: form.bull_case,
        base_case: form.base_case,
        bear_case: form.bear_case,
        key_risks: [],
        key_drivers: [],
        recommendation: '',
        confidence: 0.7,
      }) as any
      if (result?.memo_id) {
        setSelectedId(result.memo_id)
        const detail = await memoApi.get(result.memo_id) as Memo
        setMemos(prev => [detail, ...prev])
      }
    } catch {} finally { setGenerating(false) }
  }

  const handleRender = async () => {
    if (!selectedId) return
    setRendering(true)
    try {
      const data = await memoApi.render(selectedId) as any
      setRendered(data?.content || data?.markdown || JSON.stringify(data, null, 2))
    } catch {} finally { setRendering(false) }
  }

  const handleDownload = () => {
    if (!rendered || !selected) return
    const blob = new Blob([rendered], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `memo-${selected.entity}-${new Date().toISOString().slice(0, 10)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2 mb-2">
          <FileText size={14} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Investment Memo</span>
          <div className="flex-1" />
          <button onClick={fetchMemos} className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} />
          </button>
        </div>

        {/* Generate form */}
        <div className="space-y-1">
          <div className="flex gap-1">
            <input value={form.entity} onChange={e => setForm(f => ({ ...f, entity: e.target.value }))}
              placeholder="Symbol" className="w-16 h-6 px-1.5 text-[10px] rounded border outline-none"
              style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
            <input value={form.thesis} onChange={e => setForm(f => ({ ...f, thesis: e.target.value }))}
              placeholder="Thesis title" className="flex-1 h-6 px-1.5 text-[10px] rounded border outline-none"
              style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          </div>
          <textarea value={form.bull_case} onChange={e => setForm(f => ({ ...f, bull_case: e.target.value }))}
            placeholder="Bull case..." className="w-full h-8 px-1.5 py-1 text-[10px] rounded border outline-none resize-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <textarea value={form.base_case} onChange={e => setForm(f => ({ ...f, base_case: e.target.value }))}
            placeholder="Base case..." className="w-full h-8 px-1.5 py-1 text-[10px] rounded border outline-none resize-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <textarea value={form.bear_case} onChange={e => setForm(f => ({ ...f, bear_case: e.target.value }))}
            placeholder="Bear case..." className="w-full h-8 px-1.5 py-1 text-[10px] rounded border outline-none resize-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <button onClick={handleGenerate} disabled={generating}
            className="w-full h-7 rounded text-[10px] font-medium flex items-center justify-center gap-1"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {generating ? <Loader2 size={10} className="animate-spin" /> : <Plus size={10} />}
            {generating ? 'Generating...' : 'Generate Memo'}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-2">
        {selected ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>{selected.entity}</span>
              <span className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>{selected.title}</span>
            </div>

            {/* Cases */}
            {getSectionContent(selected.bull_case) && (
              <div className="p-2 rounded border" style={{ borderColor: 'var(--accent-green)' + '33', background: 'var(--accent-green)' + '08' }}>
                <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--accent-green)' }}>Bull Case</div>
                <div className="text-[10px]" style={{ color: 'var(--text-primary)' }}>{getSectionContent(selected.bull_case)}</div>
              </div>
            )}
            {getSectionContent(selected.base_case) && (
              <div className="p-2 rounded border" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--text-muted)' }}>Base Case</div>
                <div className="text-[10px]" style={{ color: 'var(--text-primary)' }}>{getSectionContent(selected.base_case)}</div>
              </div>
            )}
            {getSectionContent(selected.bear_case) && (
              <div className="p-2 rounded border" style={{ borderColor: 'var(--accent-red)' + '33', background: 'var(--accent-red)' + '08' }}>
                <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--accent-red)' }}>Bear Case</div>
                <div className="text-[10px]" style={{ color: 'var(--text-primary)' }}>{getSectionContent(selected.bear_case)}</div>
              </div>
            )}
            {getSectionContent(selected.executive_summary) && (
              <div className="p-2 rounded border" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--text-muted)' }}>Executive Summary</div>
                <div className="text-[10px]" style={{ color: 'var(--text-primary)' }}>{getSectionContent(selected.executive_summary)}</div>
              </div>
            )}

            {/* Key info */}
            {selected.key_risks && selected.key_risks.length > 0 && (
              <div>
                <div className="text-[9px] uppercase mb-0.5" style={{ color: 'var(--text-muted)' }}>Key Risks</div>
                <div className="flex flex-wrap gap-1">
                  {selected.key_risks.map((r, i) => (
                    <span key={i} className="text-[9px] px-1.5 py-0.5 rounded"
                      style={{ background: 'var(--accent-red)' + '15', color: 'var(--accent-red)' }}>{r}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-1">
              <button onClick={handleRender} disabled={rendering}
                className="flex-1 h-7 rounded text-[10px] font-medium flex items-center justify-center gap-1 border"
                style={{ borderColor: 'var(--border-primary)', color: 'var(--text-secondary)' }}>
                {rendering ? <Loader2 size={10} className="animate-spin" /> : <FileText size={10} />}
                Render Markdown
              </button>
              {rendered && (
                <button onClick={handleDownload}
                  className="h-7 px-2 rounded text-[10px] font-medium flex items-center gap-1"
                  style={{ background: 'var(--accent-green)', color: 'white' }}>
                  <Download size={10} /> Download
                </button>
              )}
            </div>

            {/* Rendered content */}
            {rendered && (
              <div className="p-2 rounded border text-[10px] whitespace-pre-wrap"
                style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-primary)', color: 'var(--text-primary)', maxHeight: 300, overflow: 'auto' }}>
                {rendered}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <FileText size={24} className="mb-2 opacity-30" />
            <div className="text-xs">Generate an investment memo</div>
          </div>
        )}
      </div>
    </div>
  )
}
