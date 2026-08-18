// FININT OMEGA — News & Alerts — wired to real monitoring + early warning APIs

import { useState, useEffect, useCallback } from 'react'
import { Newspaper, Bell, Clock, AlertTriangle, RefreshCw, Loader2 } from 'lucide-react'
import { monitoring, earlyWarning } from '../../api/client'

interface AlertItem {
  id: string
  type: string
  severity: string
  title: string
  message: string
  symbol: string
  timestamp: string
  read: boolean
}

interface WarningItem {
  warning_id: string
  type: string
  severity: string
  message: string
  symbol: string
  detected_at: string
}

const severityColor = (s: string) => {
  if (s === 'critical') return 'var(--accent-red)'
  if (s === 'warning' || s === 'high') return 'var(--accent-yellow)'
  return 'var(--accent-blue)'
}

export function NewsAlertsPanel() {
  const [activeTab, setActiveTab] = useState<'news' | 'alerts'>('news')
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [warnings, setWarnings] = useState<WarningItem[]>([])
  const [loading, setLoading] = useState(false)
  const [symbols, setSymbols] = useState('NVDA')
  const [scanning, setScanning] = useState(false)

  const fetchAlerts = useCallback(async () => {
    setLoading(true)
    try {
      const symList = symbols.split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
      const allAlerts: AlertItem[] = []
      for (const sym of symList) {
        try {
          const data = await monitoring.getAlerts(sym) as any
          const items = (data.alerts || []).map((a: any) => ({
            id: a.alert_id || a.id || Math.random().toString(36),
            type: a.alert_type || a.type || 'news',
            severity: a.severity || 'info',
            title: a.title || a.message?.slice(0, 60) || 'Alert',
            message: a.message || '',
            symbol: sym,
            timestamp: a.created_at || a.timestamp || new Date().toISOString(),
            read: false,
          }))
          allAlerts.push(...items)
        } catch {}
      }
      setAlerts(allAlerts)

      // Also fetch early warnings
      try {
        const wData = await earlyWarning.getWarnings() as any
        const warnings = (wData.warnings || []).map((w: any) => ({
          warning_id: w.warning_id || Math.random().toString(36),
          type: w.type || 'regime',
          severity: w.severity || 'info',
          message: w.message || w.description || '',
          symbol: w.symbol || '',
          detected_at: w.detected_at || w.created_at || new Date().toISOString(),
        }))
        setWarnings(warnings)
      } catch {}
    } catch {} finally {
      setLoading(false)
    }
  }, [symbols])

  useEffect(() => { fetchAlerts() }, [fetchAlerts])

  const handleScan = async () => {
    setScanning(true)
    try {
      await earlyWarning.scan({ symbols: symbols.split(',').map(s => s.trim().toUpperCase()) })
      await fetchAlerts()
    } catch {} finally { setScanning(false) }
  }

  const unreadCount = alerts.filter(a => !a.read).length

  const markRead = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, read: true } : a))
  }

  return (
    <div className="h-full flex flex-col">
      {/* Tabs */}
      <div className="flex items-center border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <button onClick={() => setActiveTab('news')}
          className="flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium border-b-2 transition-colors"
          style={{
            borderColor: activeTab === 'news' ? 'var(--accent-blue)' : 'transparent',
            color: activeTab === 'news' ? 'var(--accent-blue)' : 'var(--text-muted)',
          }}>
          <Newspaper size={12} /> News ({alerts.length})
        </button>
        <button onClick={() => setActiveTab('alerts')}
          className="flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium border-b-2 transition-colors"
          style={{
            borderColor: activeTab === 'alerts' ? 'var(--accent-blue)' : 'transparent',
            color: activeTab === 'alerts' ? 'var(--accent-blue)' : 'var(--text-muted)',
          }}>
          <Bell size={12} /> Alerts {unreadCount > 0 ? `(${unreadCount})` : ''}
        </button>
        <div className="flex-1" />
        <div className="flex items-center gap-1 pr-2">
          <input value={symbols} onChange={e => setSymbols(e.target.value)}
            placeholder="NVDA,MSFT"
            className="w-24 h-6 px-1.5 text-[9px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <button onClick={handleScan} disabled={scanning}
            className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--accent-blue)' }}>
            {scanning ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin mr-2" /> Loading...
          </div>
        ) : activeTab === 'news' ? (
          <div>
            {/* Alerts from monitoring */}
            {alerts.length > 0 ? (
              <div className="divide-y" style={{ borderColor: 'var(--border-primary)' }}>
                {alerts.map(a => (
                  <div key={a.id} onClick={() => markRead(a.id)}
                    className="px-3 py-2 hover:bg-white/[0.02] cursor-pointer"
                    style={{ opacity: a.read ? 0.6 : 1 }}>
                    <div className="flex items-start gap-2">
                      <AlertTriangle size={12} className="mt-0.5 shrink-0" style={{ color: severityColor(a.severity) }} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>{a.title}</span>
                          {a.symbol && (
                            <span className="text-[8px] px-1 rounded" style={{ background: 'var(--accent-blue)' + '22', color: 'var(--accent-blue)' }}>
                              {a.symbol}
                            </span>
                          )}
                          {!a.read && <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--accent-blue)' }} />}
                        </div>
                        <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-secondary)' }}>{a.message}</div>
                        <div className="flex items-center gap-1 mt-0.5">
                          <Clock size={9} style={{ color: 'var(--text-muted)' }} />
                          <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                            {new Date(a.timestamp).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
                <div className="text-xs mb-1">No monitoring alerts</div>
                <div className="text-[10px]">Add symbols and scan to detect alerts</div>
              </div>
            )}

            {/* Early warnings */}
            {warnings.length > 0 && (
              <div className="border-t" style={{ borderColor: 'var(--border-primary)' }}>
                <div className="text-[10px] font-semibold uppercase px-3 py-1.5"
                  style={{ color: 'var(--accent-yellow)' }}>
                  Early Warnings ({warnings.length})
                </div>
                <div className="divide-y" style={{ borderColor: 'var(--border-primary)' }}>
                  {warnings.map(w => (
                    <div key={w.warning_id} className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <AlertTriangle size={10} style={{ color: severityColor(w.severity) }} />
                        <span className="text-[10px] font-medium" style={{ color: 'var(--text-primary)' }}>
                          {w.type}: {w.message}
                        </span>
                        {w.symbol && (
                          <span className="text-[8px] px-1 rounded" style={{ background: 'var(--accent-yellow)' + '22', color: 'var(--accent-yellow)' }}>
                            {w.symbol}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: 'var(--border-primary)' }}>
            {alerts.map(a => (
              <div key={a.id} onClick={() => markRead(a.id)}
                className="px-3 py-2 cursor-pointer hover:bg-white/[0.02]"
                style={{ opacity: a.read ? 0.6 : 1 }}>
                <div className="flex items-start gap-2">
                  <AlertTriangle size={12} className="mt-0.5 shrink-0" style={{ color: severityColor(a.severity) }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>{a.title}</span>
                      {a.symbol && (
                        <span className="text-[8px] px-1 rounded" style={{ background: 'var(--accent-blue)' + '22', color: 'var(--accent-blue)' }}>
                          {a.symbol}
                        </span>
                      )}
                      {!a.read && <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--accent-blue)' }} />}
                    </div>
                    <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-secondary)' }}>{a.message}</div>
                    <div className="flex items-center gap-1 mt-0.5">
                      <Clock size={9} style={{ color: 'var(--text-muted)' }} />
                      <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                        {new Date(a.timestamp).toLocaleString()}
                      </span>
                      <span className="text-[9px] px-1 rounded" style={{ background: severityColor(a.severity) + '22', color: severityColor(a.severity) }}>
                        {a.type}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
