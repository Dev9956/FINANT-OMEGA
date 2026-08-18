// FININT OMEGA — Complete API client — every backend endpoint mapped

const BASE_URL = '/api/v1'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('finint-token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers as Record<string, string> || {}),
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem('finint-token')
    window.location.reload()
    throw new ApiError('Session expired — please log in again', 401)
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(body.detail || res.statusText, res.status)
  }
  return res.json()
}

// ── Auth ──

export const auth = {
  register: (email: string, password: string, role = 'analyst') =>
    request<{ user_id: string; email: string; role: string }>('/auth/register', {
      method: 'POST', body: JSON.stringify({ email, password, role }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST', body: JSON.stringify({ email, password }),
    }),
}

// ── System ──

export const system = {
  health: () => request<unknown>('/system/health'),
}

// ── Market ──

export const market = {
  getPrices: (symbol: string, period = '1mo', interval = '1d') =>
    request<unknown>(`/market/${symbol}/prices?period=${period}&interval=${interval}`),
  getAnalytics: (symbol: string) =>
    request<unknown>(`/market/${symbol}/analytics`),
  getIndicators: (symbol: string) =>
    request<unknown>(`/market/${symbol}/indicators`),
}

// ── Fundamentals ──

export const fundamentals = {
  getProfile: (symbol: string) =>
    request<unknown>(`/fundamentals/${symbol}`),
  getRatios: (symbol: string) =>
    request<unknown>(`/fundamentals/${symbol}/ratios`),
  getEarnings: (symbol: string) =>
    request<unknown>(`/earnings/${symbol}/analysis`),
  screening: (filters: unknown) =>
    request<unknown>('/screening/query', {
      method: 'POST', body: JSON.stringify(filters),
    }),
}

// ── Data ──

export const data = {
  getSources: () => request<unknown>('/data/sources'),
  getDatasets: () => request<unknown>('/data/datasets'),
  mock: (domain: string) => request<unknown>(`/data/mock/${domain}`),
  runPipeline: (config: unknown) =>
    request<unknown>('/data/pipeline/run', {
      method: 'POST', body: JSON.stringify(config),
    }),
}

// ── Research ──

export const research = {
  startDeep: (question: string, options?: Record<string, unknown>) =>
    request<unknown>('/research/deep', {
      method: 'POST', body: JSON.stringify({ question, depth: 'standard', ...options }),
    }),
  getStatus: (id: string) => request<unknown>(`/research/${id}`),
  getTasks: (id: string) => request<unknown>(`/research/${id}/tasks`),
  getEvidence: (id: string) => request<unknown>(`/research/${id}/evidence`),
}

// ── Agents ──

export const agents = {
  list: () => request<unknown>('/agents'),
  execute: (agentId: string, question: string, context?: unknown) =>
    request<unknown>(`/agents/${agentId}/execute`, {
      method: 'POST', body: JSON.stringify({ question, context }),
    }),
}

// ── Audit ──

export const audit = {
  getTrail: (researchId: string) => request<unknown>(`/audit/${researchId}`),
  getEvents: (researchId: string) => request<unknown>(`/audit/${researchId}/events`),
  getToolCalls: (researchId: string) => request<unknown>(`/audit/${researchId}/tool-calls`),
  export: (researchId: string) => request<unknown>(`/audit/${researchId}/export`),
}

// ── Intelligence: Thesis ──

export const thesis = {
  create: (data: unknown) =>
    request<unknown>('/intelligence/thesis', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/intelligence/thesis/${id}`),
  list: (symbol?: string) =>
    request<unknown>(`/intelligence/thesis${symbol ? `?symbol=${symbol}` : ''}`),
  update: (id: string, data: unknown) =>
    request<unknown>(`/intelligence/thesis/${id}`, {
      method: 'PUT', body: JSON.stringify(data),
    }),
  evaluate: (id: string) =>
    request<unknown>(`/intelligence/thesis/${id}/evaluate`, { method: 'POST', body: '{}' }),
  getHistory: (id: string) => request<unknown>(`/intelligence/thesis/${id}/history`),
}

// ── Intelligence: Contradictions ──

export const contradictions = {
  managementVsFinancials: (data: unknown) =>
    request<unknown>('/intelligence/contradictions/management-vs-financials', {
      method: 'POST', body: JSON.stringify(data),
    }),
  guidanceVsActual: (data: unknown) =>
    request<unknown>('/intelligence/contradictions/guidance-vs-actual', {
      method: 'POST', body: JSON.stringify(data),
    }),
  narrativeVsNumbers: (data: unknown) =>
    request<unknown>('/intelligence/contradictions/narrative-vs-numbers', {
      method: 'POST', body: JSON.stringify(data),
    }),
  earningsVsCashflow: (data: unknown) =>
    request<unknown>('/intelligence/contradictions/earnings-vs-cashflow', {
      method: 'POST', body: JSON.stringify(data),
    }),
}

// ── Intelligence: Evidence Graph ──

export const evidenceGraph = {
  addNode: (data: unknown) =>
    request<unknown>('/intelligence/evidence-graph/nodes', {
      method: 'POST', body: JSON.stringify(data),
    }),
  getNode: (id: string) => request<unknown>(`/intelligence/evidence-graph/nodes/${id}`),
  getSupporting: (id: string) => request<unknown>(`/intelligence/evidence-graph/nodes/${id}/supporting`),
  getContradicting: (id: string) => request<unknown>(`/intelligence/evidence-graph/nodes/${id}/contradicting`),
  getChain: (id: string) => request<unknown>(`/intelligence/evidence-graph/nodes/${id}/chain`),
  getConfidence: (id: string) => request<unknown>(`/intelligence/evidence-graph/nodes/${id}/confidence`),
  search: (query: string) => request<unknown>(`/intelligence/evidence-graph/search?q=${query}`),
  getStats: () => request<unknown>('/intelligence/evidence-graph/stats'),
}

// ── Intelligence: Debate ──

export const debate = {
  start: (data: unknown) =>
    request<unknown>('/intelligence/debate', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/intelligence/debate/${id}`),
}

// ── Intelligence: Causal ──

export const causal = {
  createGraph: (data: unknown) =>
    request<unknown>('/intelligence/causal/graphs', {
      method: 'POST', body: JSON.stringify(data),
    }),
  addNode: (graphId: string, data: unknown) =>
    request<unknown>(`/intelligence/causal/graphs/${graphId}/nodes`, {
      method: 'POST', body: JSON.stringify(data),
    }),
  chain: (graphId: string, data: unknown) =>
    request<unknown>(`/intelligence/causal/graphs/${graphId}/chain`, {
      method: 'POST', body: JSON.stringify(data),
    }),
  getHypothesis: (id: string) => request<unknown>(`/intelligence/causal/hypotheses/${id}`),
  evaluateHypothesis: (id: string, data: unknown) =>
    request<unknown>(`/intelligence/causal/hypotheses/${id}/evaluate`, {
      method: 'POST', body: JSON.stringify(data),
    }),
  listGraphs: () => request<unknown>('/intelligence/causal/graphs'),
  listHypotheses: () => request<unknown>('/intelligence/causal/hypotheses'),
}

// ── Intelligence: Regime ──

export const regime = {
  detect: (data: unknown) =>
    request<unknown>('/intelligence/regime/detect', {
      method: 'POST', body: JSON.stringify(data),
    }),
}

// ── Intelligence: Scenarios ──

export const scenarios = {
  create: (data: unknown) =>
    request<unknown>('/intelligence/scenarios', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/intelligence/scenarios/${id}`),
  list: () => request<unknown>('/intelligence/scenarios'),
}

// ── Intelligence: Early Warning ──

export const earlyWarning = {
  scan: (data: unknown) =>
    request<unknown>('/intelligence/early-warning/scan', {
      method: 'POST', body: JSON.stringify(data),
    }),
  getWarnings: () => request<unknown>('/intelligence/early-warning/warnings'),
}

// ── Intelligence: Anomaly ──

export const anomaly = {
  detect: (data: unknown) =>
    request<unknown>('/intelligence/anomaly/detect', {
      method: 'POST', body: JSON.stringify(data),
    }),
  getAnomalies: () => request<unknown>('/intelligence/anomaly/anomalies'),
}

// ── Intelligence: Decay ──

export const decay = {
  addEvidence: (data: unknown) =>
    request<unknown>('/intelligence/decay/evidence', {
      method: 'POST', body: JSON.stringify(data),
    }),
  score: (data: unknown) =>
    request<unknown>('/intelligence/decay/score', {
      method: 'POST', body: JSON.stringify(data),
    }),
  confirm: (evidenceId: string) =>
    request<unknown>(`/intelligence/decay/confirm/${evidenceId}`, {
      method: 'POST', body: '{}',
    }),
  getAll: () => request<unknown>('/intelligence/decay/all'),
}

// ── Intelligence: Research Loop ──

export const researchLoop = {
  run: (data: unknown) =>
    request<unknown>('/intelligence/research-loop/run', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/intelligence/research-loop/${id}`),
}

// ── Intelligence: Cross-Entity ──

export const crossEntity = {
  addEntities: (data: unknown) =>
    request<unknown>('/intelligence/cross-entity/entities', {
      method: 'POST', body: JSON.stringify(data),
    }),
  analyze: (data: unknown) =>
    request<unknown>('/intelligence/cross-entity/analyze', {
      method: 'POST', body: JSON.stringify(data),
    }),
  getResult: (id: string) => request<unknown>(`/intelligence/cross-entity/results/${id}`),
  weakeningThesis: () => request<unknown>('/intelligence/cross-entity/weakening-thesis'),
  strongCashflow: () => request<unknown>('/intelligence/cross-entity/strong-cashflow-low-valuation'),
  highAnomaly: () => request<unknown>('/intelligence/cross-entity/high-anomaly'),
}

// ── Intelligence: Predictions ──

export const predictions = {
  create: (data: unknown) =>
    request<unknown>('/intelligence/predictions', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/intelligence/predictions/${id}`),
  resolve: (id: string, data: unknown) =>
    request<unknown>(`/intelligence/predictions/${id}/resolve`, {
      method: 'POST', body: JSON.stringify(data),
    }),
  list: () => request<unknown>('/intelligence/predictions'),
  calibrationReport: () => request<unknown>('/intelligence/predictions/calibration/report'),
}

// ── Intelligence: Digital Twin ──

export const digitalTwin = {
  create: (data: unknown) =>
    request<unknown>('/intelligence/digital-twin', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/intelligence/digital-twin/${id}`),
  snapshot: (id: string) =>
    request<unknown>(`/intelligence/digital-twin/${id}/snapshot`, {
      method: 'POST', body: '{}',
    }),
  scenario: (id: string, data: unknown) =>
    request<unknown>(`/intelligence/digital-twin/${id}/scenario`, {
      method: 'POST', body: JSON.stringify(data),
    }),
  list: () => request<unknown>('/intelligence/digital-twin'),
}

// ── Intelligence: Quality ──

export const quality = {
  evaluate: (data: unknown) =>
    request<unknown>('/intelligence/quality/evaluate', {
      method: 'POST', body: JSON.stringify(data),
    }),
}

// ── Intelligence: Memo ──

export const memo = {
  generate: (data: unknown) =>
    request<unknown>('/intelligence/memo/generate', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/intelligence/memo/${id}`),
  render: (id: string) => request<unknown>(`/intelligence/memo/${id}/render`),
}

// ── Estimates ──

export const estimates = {
  create: (data: unknown) =>
    request<unknown>('/estimates', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (symbol: string) => request<unknown>(`/estimates/${symbol}`),
  getSurprise: (symbol: string) => request<unknown>(`/estimates/${symbol}/surprise`),
  getRevisions: (symbol: string) => request<unknown>(`/estimates/${symbol}/revisions`),
}

// ── Corporate Actions ──

export const corporateActions = {
  create: (data: unknown) =>
    request<unknown>('/corporate-actions', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (symbol: string) => request<unknown>(`/corporate-actions/${symbol}`),
  adjust: (data: unknown) =>
    request<unknown>('/corporate-actions/adjust', {
      method: 'POST', body: JSON.stringify(data),
    }),
}

// ── M&A Intelligence ──

export const ma = {
  addTransaction: (data: unknown) =>
    request<unknown>('/ma/transactions', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (symbol: string) => request<unknown>(`/ma/transactions/${symbol}`),
  getActive: () => request<unknown>('/ma/active'),
  getBySector: (sector: string) => request<unknown>(`/ma/sector/${sector}`),
}

// ── Monitoring ──

export const monitoring = {
  addCompany: (data: unknown) =>
    request<unknown>('/monitoring/companies', {
      method: 'POST', body: JSON.stringify(data),
    }),
  removeCompany: (symbol: string) =>
    request<unknown>(`/monitoring/companies/${symbol}`, { method: 'DELETE' }),
  triggerUpdate: () =>
    request<unknown>('/monitoring/update', { method: 'POST', body: '{}' }),
  getAlerts: (symbol: string) => request<unknown>(`/monitoring/alerts/${symbol}`),
  getState: (symbol: string) => request<unknown>(`/monitoring/state/${symbol}`),
}

// ── Change Detection ──

export const changes = {
  detect: (data: unknown) =>
    request<unknown>('/changes/detect', {
      method: 'POST', body: JSON.stringify(data),
    }),
  compare: (data: unknown) =>
    request<unknown>('/changes/compare', {
      method: 'POST', body: JSON.stringify(data),
    }),
}

// ── Grid ──

export const grid = {
  generate: (data: unknown) =>
    request<unknown>('/grid/generate', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/grid/${id}`),
}

// ── Deliverables ──

export const deliverables = {
  generate: (data: unknown) =>
    request<unknown>('/deliverables/generate', {
      method: 'POST', body: JSON.stringify(data),
    }),
  get: (id: string) => request<unknown>(`/deliverables/${id}`),
  render: (id: string) => request<unknown>(`/deliverables/${id}/render`),
}

// ── Scheduled Research ──

export const scheduled = {
  create: (data: unknown) =>
    request<unknown>('/scheduled', {
      method: 'POST', body: JSON.stringify(data),
    }),
  list: () => request<unknown>('/scheduled'),
  update: (id: string, data: unknown) =>
    request<unknown>(`/scheduled/${id}`, {
      method: 'PUT', body: JSON.stringify(data),
    }),
  remove: (id: string) =>
    request<unknown>(`/scheduled/${id}`, { method: 'DELETE' }),
  run: (id: string) =>
    request<unknown>(`/scheduled/${id}/run`, { method: 'POST', body: '{}' }),
  getRuns: () => request<unknown>('/scheduled/runs'),
}

// ── Watchlist ──

export const watchlist = {
  research: (data: unknown) =>
    request<unknown>('/watchlist/research', {
      method: 'POST', body: JSON.stringify(data),
    }),
  getStatus: (id: string) => request<unknown>(`/watchlist/research/${id}/status`),
  getResult: (id: string) => request<unknown>(`/watchlist/research/${id}`),
}

// ── Narrative ──

export const narrative = {
  analyze: (data: unknown) =>
    request<unknown>('/intelligence/narrative/analyze', {
      method: 'POST', body: JSON.stringify(data),
    }),
}

// ── Digital Twin ── (already defined above)

// ── Portfolio ──

export const portfolio = {
  addPosition: (data: unknown) =>
    request<unknown>('/portfolio/positions', {
      method: 'POST', body: JSON.stringify(data),
    }),
  listPositions: () => request<unknown>('/portfolio/positions'),
  getPosition: (id: string) => request<unknown>(`/portfolio/positions/${id}`),
  updatePosition: (id: string, data: unknown) =>
    request<unknown>(`/portfolio/positions/${id}`, {
      method: 'PUT', body: JSON.stringify(data),
    }),
  deletePosition: (id: string) =>
    request<unknown>(`/portfolio/positions/${id}`, { method: 'DELETE' }),
  getSummary: () => request<unknown>('/portfolio/summary'),
}
