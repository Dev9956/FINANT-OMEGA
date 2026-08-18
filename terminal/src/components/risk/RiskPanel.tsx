// FININT OMEGA — Risk Analysis — wired to real market analytics + anomaly detection

import { useState, useCallback } from 'react'
import { Shield, RefreshCw, Loader2, AlertTriangle } from 'lucide-react'
import { market, anomaly } from '../../api/client'

interface RiskMetrics {
  symbol: string
  volatility: number
  sharpe_ratio: number
  max_drawdown: number
  beta: number
  value_at_risk: number
}

interface AnomalyItem {
  anomaly_id: string
  metric: string
  value: number
  expected: number
  deviation: number
  severity: string
  detected_at: string
}

const SEVERITY_COLOR = (s: string) => {
  if (s === 'critical' || s === 'high') return 'var(--accent-red)'
  if (s === 'medium') return 'var(--accent-yellow)'
  return 'var(--accent-green)'
}

export function RiskPanel() {
  const [metrics, setMetrics] = useState<RiskMetrics | null>(null)
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([])
  const [loading, setLoading] = useState(false)
  const [symbol, setSymbol] = useState('NVDA')

  const analyze = useCallback(async () => {
    setLoading(true)
    try {
      // Get market analytics (volatility, Sharpe, max drawdown, CAGR)
      const analytics = await market.getAnalytics(symbol) as any

      // Get anomaly detection
      const anomalyData = await anomaly.detect({ symbol, metrics: { price_change: 0 } }) as any

      setMetrics({
        symbol: symbol.toUpperCase(),
        volatility: analytics.volatility || 0,
        sharpe_ratio: analytics.sharpe_ratio || 0,
        max_drawdown: analytics.max_drawdown || 0,
        beta: 1.0, // placeholder until we have benchmark comparison
        value_at_risk: (analytics.volatility || 0) * 1.65, // 95% VaR approximation
      })

      setAnomalies(anomalyData?.anomalies || [])
    } catch {} finally { setLoading(false) }
  }, [symbol])

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2 mb-2">
          <Shield size={14} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Risk Analysis</span>
          <div className="flex-1" />
          <button onClick={analyze} disabled={loading}
            className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        <div className="flex items-center gap-1">
          <input value={symbol} onChange={e => setSymbol(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && analyze()}
            placeholder="Symbol" className="w-16 h-7 px-1.5 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <button onClick={analyze} disabled={loading}
            className="h-7 px-2 rounded text-[10px] font-medium"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {loading ? <Loader2 size={10} className="animate-spin" /> : 'Analyze'}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-2 space-y-2">
        {loading && !metrics ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin mr-2" /> Analyzing risk...
          </div>
        ) : metrics ? (
          <>
            {/* Risk metrics */}
            <div className="grid grid-cols-2 gap-1.5">
              {[
                { label: 'Volatility', value: `${(metrics.volatility * 100).toFixed(1)}%`, color: metrics.volatility > 0.4 ? 'var(--accent-red)' : metrics.volatility > 0.25 ? 'var(--accent-yellow)' : 'var(--accent-green)' },
                { label: 'Sharpe Ratio', value: metrics.sharpe_ratio.toFixed(2), color: metrics.sharpe_ratio > 1 ? 'var(--accent-green)' : metrics.sharpe_ratio > 0.5 ? 'var(--accent-yellow)' : 'var(--accent-red)' },
                { label: 'Max Drawdown', value: `${(metrics.max_drawdown * 100).toFixed(1)}%`, color: 'var(--accent-red)' },
                { label: 'Beta', value: metrics.beta.toFixed(2), color: metrics.beta > 1.2 ? 'var(--accent-yellow)' : 'var(--accent-green)' },
                { label: '95% VaR', value: `${(metrics.value_at_risk * 100).toFixed(1)}%`, color: 'var(--accent-red)' },
                { label: 'Symbol', value: metrics.symbol, color: 'var(--accent-blue)' },
              ].map(m => (
                <div key={m.label} className="p-1.5 rounded border text-center"
                  style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
                  <div className="text-[8px] uppercase" style={{ color: 'var(--text-muted)' }}>{m.label}</div>
                  <div className="text-[11px] font-bold font-mono" style={{ color: m.color }}>{m.value}</div>
                </div>
              ))}
            </div>

            {/* Risk gauge */}
            <div className="p-2 rounded border" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
              <div className="text-[9px] uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Risk Level</div>
              <div className="h-3 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                <div className="h-full rounded-full transition-all" style={{
                  width: `${Math.min(metrics.volatility * 200, 100)}%`,
                  background: metrics.volatility > 0.4 ? 'var(--accent-red)' : metrics.volatility > 0.25 ? 'var(--accent-yellow)' : 'var(--accent-green)',
                }} />
              </div>
              <div className="flex justify-between text-[8px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                <span>Low</span><span>Medium</span><span>High</span>
              </div>
            </div>

            {/* Anomalies */}
            {anomalies.length > 0 && (
              <div>
                <div className="text-[9px] uppercase mb-1" style={{ color: 'var(--accent-yellow)' }}>
                  Detected Anomalies ({anomalies.length})
                </div>
                <div className="space-y-1">
                  {anomalies.map(a => (
                    <div key={a.anomaly_id} className="p-1.5 rounded border flex items-start gap-2"
                      style={{ borderColor: SEVERITY_COLOR(a.severity) + '33', background: SEVERITY_COLOR(a.severity) + '08' }}>
                      <AlertTriangle size={10} className="mt-0.5 shrink-0" style={{ color: SEVERITY_COLOR(a.severity) }} />
                      <div>
                        <div className="text-[10px]" style={{ color: 'var(--text-primary)' }}>{a.metric}: {a.value}</div>
                        <div className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                          Expected: {a.expected} · Deviation: {a.deviation.toFixed(2)}σ
                        </div>
                      </div>
                      <span className="text-[8px] px-1 rounded ml-auto" style={{ background: SEVERITY_COLOR(a.severity) + '22', color: SEVERITY_COLOR(a.severity) }}>
                        {a.severity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {anomalies.length === 0 && (
              <div className="text-[10px] text-center py-4" style={{ color: 'var(--text-muted)' }}>
                No anomalies detected
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <Shield size={24} className="mb-2 opacity-30" />
            <div className="text-xs">Enter a symbol and click Analyze</div>
          </div>
        )}
      </div>
    </div>
  )
}
