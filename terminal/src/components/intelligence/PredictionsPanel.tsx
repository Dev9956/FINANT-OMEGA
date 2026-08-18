// FININT OMEGA — Predictions — wired to real backend API

import { useState, useEffect, useCallback } from 'react'
import { Target, RefreshCw, Loader2, Plus } from 'lucide-react'
import { predictions } from '../../api/client'

interface Prediction {
  prediction_id: string
  entity: string
  prediction_text: string
  predicted_value: number
  confidence: number
  horizon_days: number
  metric: string
  status: string
  actual_value: number | null
  created_at: string
  resolved_at: string | null
}

interface CalibrationReport {
  total_predictions?: number
  resolved?: number
  brier_score: number
  calibration: { bucket: string; predicted: number; actual: number; count: number }[]
}

const confidenceColor = (c: number) => {
  if (c >= 0.7) return 'var(--accent-green)'
  if (c >= 0.5) return 'var(--accent-yellow)'
  return 'var(--accent-red)'
}

export function PredictionsPanel() {
  const [preds, setPreds] = useState<Prediction[]>([])
  const [calibration, setCalibration] = useState<CalibrationReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [activeTab, setActiveTab] = useState<'predictions' | 'calibration'>('predictions')
  const [form, setForm] = useState({ entity: 'NVDA', prediction_text: '', predicted_value: 0, confidence: 0.7, metric: '', horizon_days: 365 })

  const fetchPreds = useCallback(async () => {
    setLoading(true)
    try {
      const data = await predictions.list() as any
      setPreds(data.predictions || [])
    } catch {} finally { setLoading(false) }
  }, [])

  const fetchCalibration = useCallback(async () => {
    try {
      const data = await predictions.calibrationReport() as any
      setCalibration(data)
    } catch {}
  }, [])

  useEffect(() => { fetchPreds(); fetchCalibration() }, [fetchPreds, fetchCalibration])

  const handleCreate = async () => {
    if (!form.prediction_text.trim()) return
    setCreating(true)
    try {
      await predictions.create({
        entity: form.entity.toUpperCase(),
        prediction_text: form.prediction_text,
        predicted_value: form.predicted_value,
        confidence: form.confidence,
        metric: form.metric,
        horizon_days: form.horizon_days,
      })
      setForm({ entity: 'NVDA', prediction_text: '', predicted_value: 0, confidence: 0.7, metric: '', horizon_days: 365 })
      await fetchPreds()
      await fetchCalibration()
    } catch {} finally { setCreating(false) }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <button onClick={() => setActiveTab('predictions')}
          className="px-3 py-1.5 text-[10px] font-medium border-b-2"
          style={{
            borderColor: activeTab === 'predictions' ? 'var(--accent-blue)' : 'transparent',
            color: activeTab === 'predictions' ? 'var(--accent-blue)' : 'var(--text-muted)',
          }}>
          Predictions ({preds.length})
        </button>
        <button onClick={() => setActiveTab('calibration')}
          className="px-3 py-1.5 text-[10px] font-medium border-b-2"
          style={{
            borderColor: activeTab === 'calibration' ? 'var(--accent-blue)' : 'transparent',
            color: activeTab === 'calibration' ? 'var(--accent-blue)' : 'var(--text-muted)',
          }}>
          Calibration
        </button>
        <div className="flex-1" />
        <button onClick={fetchPreds} className="p-1 rounded hover:bg-white/5 mr-2" style={{ color: 'var(--text-muted)' }}>
          <RefreshCw size={12} />
        </button>
      </div>

      <div className="flex-1 overflow-auto p-2">
        {activeTab === 'predictions' ? (
          <>
            {/* Create form */}
            <div className="p-2 rounded border mb-2 space-y-1.5" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
              <div className="text-[10px] uppercase" style={{ color: 'var(--text-muted)' }}>New Prediction</div>
              <div className="flex gap-1">
                <input value={form.entity} onChange={e => setForm(f => ({ ...f, entity: e.target.value }))}
                  placeholder="Symbol" className="w-16 h-6 px-1.5 text-[10px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
                <input value={form.prediction_text} onChange={e => setForm(f => ({ ...f, prediction_text: e.target.value }))}
                  placeholder="Prediction question..." className="flex-1 h-6 px-1.5 text-[10px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
              </div>
              <div className="flex gap-1">
                <input type="number" value={form.predicted_value} onChange={e => setForm(f => ({ ...f, predicted_value: +e.target.value }))}
                  placeholder="Value" className="w-20 h-6 px-1.5 text-[10px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
                <input type="number" step="0.1" min="0" max="1" value={form.confidence} onChange={e => setForm(f => ({ ...f, confidence: +e.target.value }))}
                  placeholder="Conf" className="w-16 h-6 px-1.5 text-[10px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
                <input type="number" value={form.horizon_days} onChange={e => setForm(f => ({ ...f, horizon_days: +e.target.value }))}
                  placeholder="365d" className="w-14 h-6 px-1 text-[10px] rounded border outline-none"
                  style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
                <button onClick={handleCreate} disabled={creating}
                  className="h-6 px-2 rounded text-[10px] font-medium flex items-center gap-1"
                  style={{ background: 'var(--accent-blue)', color: 'white' }}>
                  {creating ? <Loader2 size={8} className="animate-spin" /> : <Plus size={8} />}
                  Add
                </button>
              </div>
            </div>

            {/* List */}
            {loading ? (
              <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
                <Loader2 size={14} className="animate-spin mr-2" /> Loading...
              </div>
            ) : preds.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
                <Target size={24} className="mb-2 opacity-30" />
                <div className="text-xs">No predictions yet</div>
              </div>
            ) : (
              <div className="space-y-1">
                {preds.map(p => (
                  <div key={p.prediction_id} className="p-2 rounded border flex items-start gap-2"
                    style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                    <Target size={12} className="mt-0.5 shrink-0" style={{ color: confidenceColor(p.confidence) }} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[9px] px-1 rounded" style={{ background: 'var(--accent-blue)' + '22', color: 'var(--accent-blue)' }}>
                          {p.entity}
                        </span>
                        <span className="text-xs" style={{ color: 'var(--text-primary)' }}>{p.prediction_text || (p as any).question}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-[10px]">
                        <span style={{ color: 'var(--text-muted)' }}>Predicted: {p.predicted_value}</span>
                        <span style={{ color: confidenceColor(p.confidence) }}>{(p.confidence * 100).toFixed(0)}%</span>
                        <span style={{ color: 'var(--text-muted)' }}>{p.horizon_days}d</span>
                        <span className="px-1 rounded" style={{
                          background: p.status === 'resolved' ? 'var(--accent-green)' + '22' : 'var(--accent-yellow)' + '22',
                          color: p.status === 'resolved' ? 'var(--accent-green)' : 'var(--accent-yellow)',
                        }}>
                          {p.status}
                        </span>
                        {p.actual_value != null && (
                          <span style={{ color: 'var(--accent-green)' }}>Actual: {p.actual_value}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          /* Calibration tab */
          <div className="space-y-2">
            {calibration ? (
              <>
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 rounded border text-center" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                    <div className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Total</div>
                    <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{calibration.total_predictions}</div>
                  </div>
                  <div className="p-2 rounded border text-center" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                    <div className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Resolved</div>
                    <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{calibration.resolved}</div>
                  </div>
                  <div className="p-2 rounded border text-center" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                    <div className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Brier Score</div>
                    <div className="text-sm font-bold" style={{ color: calibration.brier_score > 0 ? confidenceColor(1 - calibration.brier_score) : 'var(--text-muted)' }}>
                      {calibration.brier_score.toFixed(3)}
                    </div>
                  </div>
                </div>
                {calibration.calibration?.length > 0 && (
                  <div className="rounded border" style={{ borderColor: 'var(--border-primary)' }}>
                    <div className="text-[10px] font-semibold uppercase px-2 py-1" style={{ color: 'var(--text-muted)' }}>
                      Calibration by Bucket
                    </div>
                    {calibration.calibration.map((b, i) => (
                      <div key={i} className="flex items-center gap-2 px-2 py-1 text-[10px] border-t"
                        style={{ borderColor: 'var(--border-primary)' }}>
                        <span className="w-16" style={{ color: 'var(--text-primary)' }}>{b.bucket}</span>
                        <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                          <div className="h-full rounded-full" style={{ width: `${b.predicted * 100}%`, background: 'var(--accent-blue)' }} />
                        </div>
                        <span style={{ color: 'var(--accent-green)' }}>{(b.actual * 100).toFixed(0)}%</span>
                        <span style={{ color: 'var(--text-muted)' }}>({b.count})</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
                <Loader2 size={14} className="animate-spin mr-2" /> Loading calibration...
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
