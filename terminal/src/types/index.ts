// FININT OMEGA — Terminal core types

// ── Market Data ──

export interface Ticker {
  symbol: string
  name: string
  exchange: string
  currency: string
  price: number
  change: number
  changePercent: number
  volume: number
  marketCap?: number
  pe?: number
  pb?: number
  dividendYield?: number
  high52w?: number
  low52w?: number
  updatedAt: string
}

export interface OHLCV {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface CompanyProfile {
  symbol: string
  name: string
  exchange: string
  currency: string
  sector: string
  industry: string
  country: string
  employees?: number
  description?: string
  website?: string
  ceo?: string
  founded?: string
}

// ── Financials ──

export interface FinancialStatement {
  symbol: string
  periodEnd: string
  statementType: 'income_statement' | 'balance_sheet' | 'cash_flow'
  fiscalYear: number
  fiscalQuarter: number
  currency: string
  revenue: number
  netIncome: number
  epsDiluted: number
  totalAssets: number
  totalEquity: number
  freeCashFlow: number
}

export interface FinancialRatios {
  symbol: string
  date: string
  peRatio: number
  pbRatio: number
  evEbitda: number
  roe: number
  roce: number
  roa: number
  grossMargin: number
  operatingMargin: number
  netMargin: number
  debtEquity: number
  currentRatio: number
  revenueGrowthYoy: number
  earningsGrowthYoy: number
}

// ── Research ──

export interface ResearchSession {
  id: string
  question: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  createdAt: string
  completedAt?: string
  evidenceCount: number
  confidence?: number
  summary?: string
  thesis?: Thesis
  contradictions: Contradiction[]
}

export interface Thesis {
  id: string
  symbol: string
  direction: 'bull' | 'bear' | 'neutral'
  title: string
  hypothesis: string
  confidence: number
  evidenceCount: number
  contradictionsCount: number
  createdAt: string
  updatedAt: string
  versions: ThesisVersion[]
}

export interface ThesisVersion {
  version: number
  hypothesis: string
  confidence: number
  evidenceIds: string[]
  createdAt: string
  changeReason: string
}

export interface Contradiction {
  id: string
  type: 'management_vs_financials' | 'guidance_vs_actual' | 'narrative_vs_numbers' | 'earnings_vs_cashflow'
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  leftClaim: EvidenceClaim
  rightClaim: EvidenceClaim
}

export interface EvidenceClaim {
  id: string
  statement: string
  source: string
  sourceType: string
  confidence: number
  value?: number
}

// ── Evidence Graph ──

export interface EvidenceNode {
  id: string
  type: 'claim' | 'data_point' | 'document' | 'calculation'
  label: string
  value?: number
  source: string
  confidence: number
}

export interface EvidenceEdge {
  from: string
  to: string
  relationship: 'supports' | 'contradicts' | 'derives_from' | 'references'
}

export interface EvidenceGraph {
  nodes: EvidenceNode[]
  edges: EvidenceEdge[]
}

// ── Screener ──

export interface ScreenerFilter {
  field: string
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte' | 'between' | 'contains'
  value: number | string | [number, number]
}

export interface ScreenerResult {
  symbol: string
  name: string
  price: number
  changePercent: number
  marketCap: number
  pe: number
  revenueGrowth: number
  roe: number
}

// ── Workspace ──

export type PanelType =
  | 'market-overview'
  | 'ticker-detail'
  | 'company-intelligence'
  | 'company-profile'
  | 'financials'
  | 'ratios'
  | 'chart'
  | 'research'
  | 'evidence'
  | 'thesis'
  | 'screener'
  | 'portfolio'
  | 'risk'
  | 'news'
  | 'alerts'
  | 'ai-chat'
  | 'scenario'
  | 'debate'
  | 'regime'
  | 'early-warning'
  | 'anomaly'
  | 'decay'
  | 'cross-entity'
  | 'predictions'
  | 'digital-twin'
  | 'quality'
  | 'memo'
  | 'integrations'

export interface Panel {
  id: string
  type: PanelType
  title: string
  props: Record<string, unknown>
  position: { x: number; y: number; w: number; h: number }
}

export interface Workspace {
  id: string
  name: string
  icon: string
  layout: Panel[]
  createdAt: string
  updatedAt: string
}

// ── User ──

export interface User {
  id: string
  email: string
  role: 'admin' | 'manager' | 'analyst' | 'viewer'
  orgId?: string
}

// ── API Responses ──

export interface ApiResponse<T> {
  data: T
  requestId?: string
  duration?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

// ── WebSocket Messages ──

export type WSMessage =
  | { type: 'ticker_update'; data: Partial<Ticker> }
  | { type: 'research_progress'; data: { sessionId: string; stage: string; progress: number } }
  | { type: 'alert'; data: { id: string; type: string; message: string; severity: string; timestamp: string } }
  | { type: 'pong' }
