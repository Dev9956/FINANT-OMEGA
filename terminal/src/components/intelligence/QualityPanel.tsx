// FININT OMEGA — Research Quality Score — wired to real backend API

import { useState } from 'react'
import { Award, Loader2 } from 'lucide-react'
import { quality } from '../../api/client'

interface QualityReport {
  overall_score: number
  grade: string
  dimensions: {
    evidence_count: number
    source_quality: number
    numerical_accuracy: number
    freshness: number
    contradictions: number
    completeness: number
    uncertainty_disclosed: boolean
    reproducible: boolean
  }
}

const gradeColor = (g: string) => {
  if (g === 'A') return 'var(--accent-green)'
  if (g === 'B') return 'var(--accent-blue)'
  if (g === 'C') return 'var(--accent-yellow)'
  return 'var(--accent-red)'
}

export function QualityPanel() {
  const [report, setReport] = useState<QualityReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    evidence_count: 10,
    source_quality: 0.8,
    numerical_accuracy: 0.9,
    freshness: 0.7,
    contradictions: 1,
    completeness: 0.85,
    uncertainty_disclosed: true,
    reproducible: true,
  })

  const handleEvaluate = async () => {
    setLoading(true)
    try {
      const result = await quality.evaluate(form) as any
      setReport({
        overall_score: result.overall_score || 0,
        grade: result.grade || 'N/A',
        dimensions: {
          evidence_count: form.evidence_count,
          source_quality: result.dimension_scores?.source_quality || form.source_quality,
          numerical_accuracy: result.dimension_scores?.numerical_accuracy || form.numerical_accuracy,
          freshness: result.dimension_scores?.freshness || form.freshness,
          contradictions: form.contradictions,
          completeness: result.dimension_scores?.completeness || form.completeness,
          uncertainty_disclosed: form.uncertainty_disclosed,
          reproducible: form.reproducible,
        },
      })
    } catch {} finally { setLoading(false) }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2 mb-2">
          <Award size={14} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Research Quality Score</span>
        </div>

        {/* Input form */}
        <div className="space-y-1.5">
          <div className="grid grid-cols-2 gap-1.5">
            <div>
              <label className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Evidence Count</label>
              <input type="number" value={form.evidence_count} onChange={e => setForm(f => ({ ...f, evidence_count: +e.target.value }))}
                className="w-full h-6 px-1.5 text-[10px] rounded border outline-none"
                style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Contradictions</label>
              <input type="number" value={form.contradictions} onChange={e => setForm(f => ({ ...f, contradictions: +e.target.value }))}
                className="w-full h-6 px-1.5 text-[10px] rounded border outline-none"
                style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
            </div>
          </div>
          {[
            { key: 'source_quality', label: 'Source Quality' },
            { key: 'numerical_accuracy', label: 'Numerical Accuracy' },
            { key: 'freshness', label: 'Freshness' },
            { key: 'completeness', label: 'Completeness' },
          ].map(d => (
            <div key={d.key}>
              <div className="flex justify-between text-[9px]" style={{ color: 'var(--text-muted)' }}>
                <span>{d.label}</span>
                <span>{((form as any)[d.key] * 100).toFixed(0)}%</span>
              </div>
              <input type="range" min="0" max="1" step="0.05"
                value={(form as any)[d.key]}
                onChange={e => setForm(f => ({ ...f, [d.key]: +e.target.value }))}
                className="w-full h-1" />
            </div>
          ))}
          <div className="flex gap-2 text-[9px]">
            <label className="flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
              <input type="checkbox" checked={form.uncertainty_disclosed}
                onChange={e => setForm(f => ({ ...f, uncertainty_disclosed: e.target.checked }))} />
              Uncertainty Disclosed
            </label>
            <label className="flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
              <input type="checkbox" checked={form.reproducible}
                onChange={e => setForm(f => ({ ...f, reproducible: e.target.checked }))} />
              Reproducible
            </label>
          </div>
          <button onClick={handleEvaluate} disabled={loading}
            className="w-full h-7 rounded text-[10px] font-medium flex items-center justify-center gap-1"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {loading ? <Loader2 size={10} className="animate-spin" /> : <Award size={10} />}
            {loading ? 'Evaluating...' : 'Evaluate Quality'}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-auto p-2">
        {report ? (
          <div className="space-y-2">
            {/* Score */}
            <div className="text-center p-3 rounded border" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
              <div className="text-3xl font-bold font-mono" style={{ color: gradeColor(report.grade) }}>
                {report.grade}
              </div>
              <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                Score: {(report.overall_score * 100).toFixed(0)}/100
              </div>
              <div className="h-2 rounded-full overflow-hidden mt-2" style={{ background: 'var(--bg-tertiary)' }}>
                <div className="h-full rounded-full" style={{
                  width: `${report.overall_score * 100}%`,
                  background: gradeColor(report.grade),
                }} />
              </div>
            </div>

            {/* Dimensions */}
            <div className="space-y-1">
              {[
                { key: 'source_quality', label: 'Source Quality', value: report.dimensions.source_quality },
                { key: 'numerical_accuracy', label: 'Numerical Accuracy', value: report.dimensions.numerical_accuracy },
                { key: 'freshness', label: 'Freshness', value: report.dimensions.freshness },
                { key: 'completeness', label: 'Completeness', value: report.dimensions.completeness },
              ].map(d => (
                <div key={d.key} className="flex items-center gap-2">
                  <span className="text-[10px] w-28" style={{ color: 'var(--text-muted)' }}>{d.label}</span>
                  <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                    <div className="h-full rounded-full" style={{ width: `${d.value * 100}%`, background: gradeColor(d.value >= 0.7 ? 'A' : d.value >= 0.5 ? 'B' : 'C') }} />
                  </div>
                  <span className="text-[10px] font-mono w-8 text-right" style={{ color: 'var(--text-primary)' }}>
                    {(d.value * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>

            {/* Flags */}
            <div className="flex gap-2 text-[10px]">
              <span className="px-1.5 py-0.5 rounded" style={{
                background: report.dimensions.uncertainty_disclosed ? 'var(--accent-green)' + '22' : 'var(--accent-red)' + '22',
                color: report.dimensions.uncertainty_disclosed ? 'var(--accent-green)' : 'var(--accent-red)',
              }}>
                Uncertainty: {report.dimensions.uncertainty_disclosed ? 'Yes' : 'No'}
              </span>
              <span className="px-1.5 py-0.5 rounded" style={{
                background: report.dimensions.reproducible ? 'var(--accent-green)' + '22' : 'var(--accent-red)' + '22',
                color: report.dimensions.reproducible ? 'var(--accent-green)' : 'var(--accent-red)',
              }}>
                Reproducible: {report.dimensions.reproducible ? 'Yes' : 'No'}
              </span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <Award size={24} className="mb-2 opacity-30" />
            <div className="text-xs">Configure parameters and evaluate</div>
          </div>
        )}
      </div>
    </div>
  )
}
