// FININT OMEGA — Integration Control Center

import { useState, useEffect, useCallback } from 'react'
import {
  Settings, Plug, CheckCircle, XCircle, AlertTriangle, RefreshCw,
  Server, Brain, Database, Globe, Activity,
  ChevronRight, ChevronDown, Zap
} from 'lucide-react'
import { request } from '../../api/client'

interface Provider {
  provider_id: string
  provider_type: string
  name: string
  description: string
  enabled: boolean
  priority: number
  config: Record<string, any>
  health: {
    status: string
    latency_ms: number
    success_rate: number
    last_checked: number
    error_message: string
    extra: Record<string, any>
  }
}

const TYPE_ICONS: Record<string, any> = {
  ai: Brain,
  market_data: Globe,
  document: Settings,
  macro: Activity,
  database: Database,
  storage: Server,
  notification: Zap,
  embedding: Zap,
}

const TYPE_LABELS: Record<string, string> = {
  ai: 'AI Providers',
  market_data: 'Market Data',
  document: 'Documents & Filings',
  macro: 'Macro Data',
  database: 'Databases',
  storage: 'Storage & Cache',
  notification: 'Notifications',
  embedding: 'Embeddings',
}

const STATUS_COLORS: Record<string, string> = {
  connected: 'var(--accent-green)',
  running: 'var(--accent-green)',
  healthy: 'var(--accent-green)',
  degraded: 'var(--accent-yellow)',
  disconnected: 'var(--text-muted)',
  disabled: 'var(--text-muted)',
  error: 'var(--accent-red)',
}

function StatusDot({ status }: { status: string }) {
  return (
    <div className="w-2 h-2 rounded-full shrink-0" style={{ background: STATUS_COLORS[status] || 'var(--text-muted)' }} />
  )
}

function ProviderCard({
  provider,
  onTest,
  onToggle,
  onUpdateConfig,
  testing,
}: {
  provider: Provider
  onTest: (id: string) => void
  onToggle: (id: string, enabled: boolean) => void
  onUpdateConfig: (id: string, config: Record<string, any>) => void
  testing: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const [configEdit, setConfigEdit] = useState(JSON.stringify(provider.config, null, 2))
  const Icon = TYPE_ICONS[provider.provider_type] || Plug
  const h = provider.health
  const statusColor = STATUS_COLORS[h.status] || 'var(--text-muted)'

  return (
    <div className="rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
      {/* Header */}
      <div className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-white/[0.02]"
        onClick={() => setExpanded(!expanded)}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: statusColor + '15' }}>
          <Icon size={16} style={{ color: statusColor }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{provider.name}</span>
            <StatusDot status={h.status} />
            <span className="text-[10px]" style={{ color: statusColor }}>{h.status}</span>
          </div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{provider.description}</div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {h.latency_ms > 0 && (
            <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>{h.latency_ms}ms</span>
          )}
          <button onClick={(e) => { e.stopPropagation(); onToggle(provider.provider_id, !provider.enabled) }}
            className="w-8 h-4 rounded-full transition-colors relative"
            style={{ background: provider.enabled ? 'var(--accent-green)' : 'var(--bg-tertiary)' }}>
            <div className="w-3 h-3 rounded-full bg-white absolute top-0.5 transition-transform"
              style={{ left: provider.enabled ? '18px' : '2px' }} />
          </button>
          {expanded ? <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} /> : <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-3 pb-3 space-y-3 border-t" style={{ borderColor: 'var(--border-primary)' }}>
          {/* Health details */}
          <div className="grid grid-cols-3 gap-2 pt-2">
            <div className="text-center p-2 rounded" style={{ background: 'var(--bg-primary)' }}>
              <div className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Status</div>
              <div className="text-xs font-medium mt-0.5" style={{ color: statusColor }}>{h.status}</div>
            </div>
            <div className="text-center p-2 rounded" style={{ background: 'var(--bg-primary)' }}>
              <div className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Latency</div>
              <div className="text-xs font-mono mt-0.5" style={{ color: 'var(--text-primary)' }}>{h.latency_ms || '—'}ms</div>
            </div>
            <div className="text-center p-2 rounded" style={{ background: 'var(--bg-primary)' }}>
              <div className="text-[9px] uppercase" style={{ color: 'var(--text-muted)' }}>Last Check</div>
              <div className="text-xs mt-0.5" style={{ color: 'var(--text-primary)' }}>
                {h.last_checked ? new Date(h.last_checked * 1000).toLocaleTimeString() : 'Never'}
              </div>
            </div>
          </div>

          {h.error_message && (
            <div className="p-2 rounded text-[10px]" style={{ background: 'var(--accent-red)' + '11', color: 'var(--accent-red)' }}>
              {h.error_message}
            </div>
          )}

          {/* Config editor */}
          <div>
            <div className="text-[10px] uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Configuration</div>
            <textarea
              value={configEdit}
              onChange={(e) => setConfigEdit(e.target.value)}
              className="w-full h-24 px-2 py-1.5 text-[10px] font-mono rounded border outline-none resize-none"
              style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}
            />
            <button onClick={() => {
              try { onUpdateConfig(provider.provider_id, JSON.parse(configEdit)) } catch {}
            }}
              className="mt-1 h-6 px-2 rounded text-[10px] border"
              style={{ borderColor: 'var(--border-primary)', color: 'var(--text-secondary)' }}>
              Save Config
            </button>
          </div>

          {/* Actions */}
          <div className="flex gap-1">
            <button onClick={() => onTest(provider.provider_id)} disabled={testing}
              className="flex-1 h-7 rounded text-[10px] font-medium flex items-center justify-center gap-1"
              style={{ background: 'var(--accent-blue)', color: 'white' }}>
              {testing ? <RefreshCw size={10} className="animate-spin" /> : <Zap size={10} />}
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export function IntegrationCenter() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<any>(null)
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [summary, setSummary] = useState<any>(null)

  // Secret Modal State
  const [showSecretModal, setShowSecretModal] = useState(false)
  const [secretProviderId, setSecretProviderId] = useState('openai')
  const [secretKeyName, setSecretKeyName] = useState('api_key')
  const [secretValue, setSecretValue] = useState('')
  const [secretStatus, setSecretStatus] = useState<string | null>(null)
  const [savingSecret, setSavingSecret] = useState(false)

  const fetchProviders = useCallback(async () => {
    try {
      const data = await request<any>('/integrations')
      setProviders(data.providers || [])
    } catch {
      // keep current
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchSummary = useCallback(async () => {
    try {
      const data = await request<any>('/integrations/health/summary')
      setSummary(data)
    } catch {}
  }, [])

  useEffect(() => {
    fetchProviders()
    fetchSummary()
  }, [fetchProviders, fetchSummary])

  const testProvider = async (id: string) => {
    setTestingId(id)
    setTestResults(null)
    try {
      const res = await request<any>(`/integrations/${id}/test`, {
        method: 'POST', body: '{}',
      })
      setTestResults(res)
    } catch (e: any) {
      setTestResults({ success: false, error: e.message })
    } finally {
      setTestingId(null)
      fetchProviders()
    }
  }

  const toggleProvider = async (id: string, enabled: boolean) => {
    try {
      await request(`/integrations/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ enabled }),
      })
      fetchProviders()
    } catch {}
  }

  const updateConfig = async (id: string, config: Record<string, any>) => {
    try {
      await request(`/integrations/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ config }),
      })
      fetchProviders()
    } catch {}
  }

  const handleSaveSecret = async () => {
    if (!secretValue.trim()) return
    setSavingSecret(true)
    setSecretStatus(null)
    try {
      const res = await request<any>(`/integrations/${secretProviderId}/secrets`, {
        method: 'POST',
        body: JSON.stringify({ secret_key: secretKeyName, secret_value: secretValue }),
      })
      setSecretStatus(`Secret saved successfully! Masked: ${res.masked}`)
      setSecretValue('')
      fetchProviders()
    } catch (e: any) {
      setSecretStatus(`Failed: ${e.message}`)
    } finally {
      setSavingSecret(false)
    }
  }

  const categories = [...new Set(providers.map(p => p.provider_type))]
  const filtered = activeCategory === 'all' ? providers : providers.filter(p => p.provider_type === activeCategory)

  return (
    <div className="h-full flex flex-col relative">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2">
          <Plug size={16} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>Integration Center</span>
        </div>
        <div className="flex items-center gap-2">
          {summary && (
            <div className="flex items-center gap-3 text-[10px]" style={{ color: 'var(--text-muted)' }}>
              <span className="flex items-center gap-1"><CheckCircle size={10} style={{ color: 'var(--accent-green)' }} />{summary.connected}</span>
              <span className="flex items-center gap-1"><XCircle size={10} style={{ color: 'var(--accent-red)' }} />{summary.disconnected}</span>
              <span className="flex items-center gap-1"><AlertTriangle size={10} style={{ color: 'var(--text-muted)' }} />{summary.disabled}</span>
            </div>
          )}
          <button onClick={() => setShowSecretModal(true)}
            className="px-2.5 py-1 rounded text-xs font-medium transition-colors"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            Set API Key
          </button>
          <button onClick={() => { setLoading(true); fetchProviders(); fetchSummary() }}
            className="p-1.5 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Secret Modal */}
      {showSecretModal && (
        <div className="absolute inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-96 rounded-lg border p-4 space-y-3" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
            <div className="flex items-center justify-between border-b pb-2" style={{ borderColor: 'var(--border-primary)' }}>
              <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>Configure Integration Secret</span>
              <button onClick={() => { setShowSecretModal(false); setSecretStatus(null) }}
                className="text-xs" style={{ color: 'var(--text-muted)' }}>✕</button>
            </div>

            <div>
              <label className="text-[10px] uppercase block mb-1" style={{ color: 'var(--text-muted)' }}>Provider</label>
              <select
                value={secretProviderId}
                onChange={(e) => setSecretProviderId(e.target.value)}
                className="w-full h-8 px-2 text-xs rounded border outline-none"
                style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}
              >
                {providers.map(p => (
                  <option key={p.provider_id} value={p.provider_id}>{p.name} ({p.provider_id})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] uppercase block mb-1" style={{ color: 'var(--text-muted)' }}>Secret Key Name</label>
              <input
                type="text"
                value={secretKeyName}
                onChange={(e) => setSecretKeyName(e.target.value)}
                placeholder="e.g. api_key"
                className="w-full h-8 px-2 text-xs rounded border outline-none"
                style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}
              />
            </div>

            <div>
              <label className="text-[10px] uppercase block mb-1" style={{ color: 'var(--text-muted)' }}>API Secret Value</label>
              <input
                type="password"
                value={secretValue}
                onChange={(e) => setSecretValue(e.target.value)}
                placeholder="Enter API Key / Token..."
                className="w-full h-8 px-2 text-xs rounded border outline-none"
                style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}
              />
            </div>

            {secretStatus && (
              <div className="text-[10px] p-2 rounded" style={{
                background: secretStatus.startsWith('Secret saved') ? 'var(--accent-green)15' : 'var(--accent-red)15',
                color: secretStatus.startsWith('Secret saved') ? 'var(--accent-green)' : 'var(--accent-red)',
              }}>
                {secretStatus}
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <button onClick={handleSaveSecret} disabled={savingSecret || !secretValue.trim()}
                className="flex-1 h-8 rounded text-xs font-medium flex items-center justify-center gap-1"
                style={{ background: 'var(--accent-blue)', color: 'white', opacity: !secretValue.trim() ? 0.5 : 1 }}>
                {savingSecret ? <RefreshCw size={12} className="animate-spin" /> : 'Save Secret Key'}
              </button>
              <button onClick={() => setShowSecretModal(false)}
                className="px-3 h-8 rounded text-xs border"
                style={{ borderColor: 'var(--border-primary)', color: 'var(--text-secondary)' }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Category tabs */}
      <div className="flex gap-1 px-4 py-2 border-b overflow-x-auto" style={{ borderColor: 'var(--border-primary)' }}>
        <button onClick={() => setActiveCategory('all')}
          className="px-2.5 py-1 rounded text-[10px] font-medium whitespace-nowrap"
          style={{
            background: activeCategory === 'all' ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
            color: activeCategory === 'all' ? 'white' : 'var(--text-muted)',
          }}>
          All ({providers.length})
        </button>
        {categories.map(cat => {
          const Icon = TYPE_ICONS[cat] || Plug
          const count = providers.filter(p => p.provider_type === cat).length
          return (
            <button key={cat} onClick={() => setActiveCategory(cat)}
              className="flex items-center gap-1 px-2.5 py-1 rounded text-[10px] font-medium whitespace-nowrap"
              style={{
                background: activeCategory === cat ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                color: activeCategory === cat ? 'white' : 'var(--text-muted)',
              }}>
              <Icon size={10} />
              {TYPE_LABELS[cat] || cat} ({count})
            </button>
          )
        })}
      </div>

      {/* Test results */}
      {testResults && (
        <div className="mx-4 mt-3 p-3 rounded-lg border" style={{
          borderColor: testResults.success ? 'var(--accent-green)' : 'var(--accent-red)',
          background: (testResults.success ? 'var(--accent-green)' : 'var(--accent-red)') + '08',
        }}>
          <div className="flex items-center gap-2 mb-1">
            {testResults.success ? <CheckCircle size={14} style={{ color: 'var(--accent-green)' }} /> : <XCircle size={14} style={{ color: 'var(--accent-red)' }} />}
            <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
              {testResults.name || testResults.provider_id}: {testResults.success ? 'ALL TESTS PASSED' : 'TESTS FAILED'}
            </span>
            {testResults.latency_ms && (
              <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>{testResults.latency_ms}ms</span>
            )}
          </div>
          {testResults.tests?.map((t: any, i: number) => (
            <div key={i} className="flex items-center gap-2 ml-5 text-[10px]">
              {t.passed ? <CheckCircle size={10} style={{ color: 'var(--accent-green)' }} /> : <XCircle size={10} style={{ color: 'var(--accent-red)' }} />}
              <span style={{ color: 'var(--text-primary)' }}>{t.name}</span>
              <span style={{ color: 'var(--text-muted)' }}>{t.detail}</span>
            </div>
          ))}
          {testResults.error && (
            <div className="ml-5 text-[10px]" style={{ color: 'var(--accent-red)' }}>{testResults.error}</div>
          )}
        </div>
      )}

      {/* Provider list */}
      <div className="flex-1 overflow-auto p-4 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center h-32" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={16} className="animate-spin mr-2" /> Loading integrations...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex items-center justify-center h-32" style={{ color: 'var(--text-muted)' }}>
            No integrations found
          </div>
        ) : (
          filtered.map(p => (
            <ProviderCard
              key={p.provider_id}
              provider={p}
              onTest={testProvider}
              onToggle={toggleProvider}
              onUpdateConfig={updateConfig}
              testing={testingId === p.provider_id}
            />
          ))
        )}
      </div>
    </div>
  )
}
