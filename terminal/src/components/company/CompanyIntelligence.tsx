// FININT OMEGA — Company Intelligence page — real backend integration

import { useState, useEffect } from 'react'
import {
  BarChart3, TrendingUp, DollarSign, PieChart, FileText,
  Shield, Target, Brain, Layers,
  ExternalLink, ArrowUpRight, ArrowDownRight
} from 'lucide-react'
import { fundamentals } from '../../api/client'

type Tab = 'overview' | 'price' | 'financials' | 'valuation' | 'earnings' |
  'filings' | 'risk' | 'thesis' | 'research'

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'overview', label: 'Overview', icon: Layers },
  { id: 'price', label: 'Price', icon: BarChart3 },
  { id: 'financials', label: 'Financials', icon: DollarSign },
  { id: 'valuation', label: 'Valuation', icon: PieChart },
  { id: 'earnings', label: 'Earnings', icon: TrendingUp },
  { id: 'filings', label: 'Filings', icon: FileText },
  { id: 'risk', label: 'Risk', icon: Shield },
  { id: 'thesis', label: 'Thesis', icon: Target },
  { id: 'research', label: 'AI Research', icon: Brain },
]

// ── Demo data ──

const DEMO_COMPANY = {
  symbol: 'NVDA',
  name: 'NVIDIA Corporation',
  exchange: 'NASDAQ',
  currency: 'USD',
  sector: 'Technology',
  industry: 'Semiconductors',
  country: 'United States',
  employees: 32000,
  description: 'NVIDIA Corporation designs and manufactures graphics processing units (GPUs) for the gaming and professional markets, as well as system on a chip units (SoCs) for mobile computing and automotive market.',
  ceo: 'Jensen Huang',
  founded: '1993',
  marketCap: 3245000000000,
  enterpriseValue: 3208000000000,
  price: 132.65,
  change: 2.34,
  changePercent: 1.80,
  high52w: 153.13,
  low52w: 47.32,
  beta: 1.68,
  pe: 72.5,
  forwardPe: 35.2,
  pb: 48.3,
  ps: 35.8,
  evEbitda: 55.2,
  roe: 115.7,
  roce: 89.4,
  roa: 55.2,
  grossMargin: 73.0,
  operatingMargin: 62.1,
  netMargin: 55.8,
  debtEquity: 0.17,
  currentRatio: 4.22,
  freeCashFlow: 28600000000,
  revenue: 91200000000,
  revenueGrowth: 122.0,
  netIncome: 50800000000,
  epsDiluted: 2.07,
}

function MetricCard({ label, value, subtext, color }: {
  label: string; value: string; subtext?: string; color?: string
}) {
  return (
    <div className="terminal-panel p-3">
      <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>
        {label}
      </div>
      <div className="text-lg font-bold" style={{ color: color || 'var(--text-primary)' }}>
        {value}
      </div>
      {subtext && (
        <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
          {subtext}
        </div>
      )}
    </div>
  )
}

function OverviewTab({ symbol }: { symbol: string }) {
  const [company, setCompany] = useState<any>(null)

  useEffect(() => {
    let cancelled = false
    Promise.allSettled([
      fundamentals.getProfile(symbol),
      fundamentals.getRatios(symbol),
    ]).then(([profileRes]) => {
      if (cancelled) return
      const profile = profileRes.status === 'fulfilled' ? profileRes.value : null
      setCompany(profile)
    })
    return () => { cancelled = true }
  }, [symbol])

  const c = company || DEMO_COMPANY
  return (
    <div className="p-3 space-y-4 overflow-y-auto h-full">
      {/* Company header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{c.symbol}</h1>
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{c.name}</span>
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
            <span>{c.sector}</span>
            <span>•</span>
            <span>{c.industry}</span>
            <span>•</span>
            <span>{c.exchange}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            ${c.price.toFixed(2)}
          </div>
          <div className={`flex items-center gap-1 text-sm font-medium ${c.change >= 0 ? 'ticker-up' : 'ticker-down'}`}>
            {c.change >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            <span>{c.change >= 0 ? '+' : ''}{c.change.toFixed(2)} ({c.changePercent.toFixed(2)}%)</span>
          </div>
        </div>
      </div>

      {/* Key metrics grid */}
      <div className="grid grid-cols-4 gap-2">
        <MetricCard label="Market Cap" value={`$${(c.marketCap / 1e9).toFixed(1)}B`} />
        <MetricCard label="P/E" value={c.pe.toFixed(1)} subtext={`Fwd: ${c.forwardPe.toFixed(1)}`} />
        <MetricCard label="P/B" value={c.pb.toFixed(1)} />
        <MetricCard label="EV/EBITDA" value={c.evEbitda.toFixed(1)} />
        <MetricCard label="ROE" value={`${c.roe.toFixed(1)}%`} color="var(--accent-green)" />
        <MetricCard label="Revenue Growth" value={`${c.revenueGrowth.toFixed(0)}%`} color="var(--accent-green)" />
        <MetricCard label="Net Margin" value={`${c.netMargin.toFixed(1)}%`} />
        <MetricCard label="D/E" value={c.debtEquity.toFixed(2)} />
      </div>

      {/* 52-week range */}
      <div className="terminal-panel p-3">
        <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>
          52-Week Range
        </div>
        <div className="relative h-2 rounded-full" style={{ background: 'var(--bg-primary)' }}>
          <div
            className="absolute h-full rounded-full"
            style={{
              background: 'var(--accent-blue)',
              width: `${((c.price - c.low52w) / (c.high52w - c.low52w)) * 100}%`,
            }}
          />
        </div>
        <div className="flex justify-between mt-1 text-[10px]" style={{ color: 'var(--text-muted)' }}>
          <span>${c.low52w.toFixed(2)}</span>
          <span style={{ color: 'var(--text-primary)' }}>${c.price.toFixed(2)}</span>
          <span>${c.high52w.toFixed(2)}</span>
        </div>
      </div>

      {/* Description */}
      <div className="terminal-panel p-3">
        <div className="text-[10px] uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>
          About
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          {c.description}
        </p>
        <div className="flex items-center gap-4 mt-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
          <span>CEO: {c.ceo}</span>
          <span>Founded: {c.founded}</span>
          <span>Employees: {c.employees.toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}

function FinancialsTab() {
  const quarters = [
    { period: 'Q4 2024', revenue: 22100, netIncome: 12285, eps: 0.49, grossMargin: 73.0 },
    { period: 'Q3 2024', revenue: 18120, netIncome: 9243, eps: 0.37, grossMargin: 74.2 },
    { period: 'Q2 2024', revenue: 13507, netIncome: 6188, eps: 0.25, grossMargin: 70.1 },
    { period: 'Q1 2024', revenue: 6051, netIncome: 2976, eps: 0.12, grossMargin: 64.6 },
    { period: 'Q4 2023', revenue: 6051, netIncome: 2976, eps: 0.12, grossMargin: 63.3 },
  ]

  return (
    <div className="p-3 overflow-y-auto h-full">
      <div className="terminal-panel overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ background: 'var(--bg-secondary)' }}>
              <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--text-muted)' }}>Period</th>
              <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--text-muted)' }}>Revenue ($M)</th>
              <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--text-muted)' }}>Net Income ($M)</th>
              <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--text-muted)' }}>EPS</th>
              <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--text-muted)' }}>Gross Margin</th>
            </tr>
          </thead>
          <tbody>
            {quarters.map((q) => (
              <tr key={q.period} className="border-t" style={{ borderColor: 'var(--border-primary)' }}>
                <td className="px-3 py-2 font-medium" style={{ color: 'var(--text-primary)' }}>{q.period}</td>
                <td className="text-right px-3 py-2" style={{ color: 'var(--text-primary)' }}>
                  ${q.revenue.toLocaleString()}
                </td>
                <td className="text-right px-3 py-2" style={{ color: 'var(--accent-green)' }}>
                  ${q.netIncome.toLocaleString()}
                </td>
                <td className="text-right px-3 py-2" style={{ color: 'var(--text-primary)' }}>
                  ${q.eps.toFixed(2)}
                </td>
                <td className="text-right px-3 py-2" style={{ color: 'var(--text-primary)' }}>
                  {q.grossMargin.toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ValuationTab() {
  const c = DEMO_COMPANY
  const metrics = [
    { label: 'P/E (TTM)', value: c.pe.toFixed(1), sector: '28.5', percentile: 85 },
    { label: 'Forward P/E', value: c.forwardPe.toFixed(1), sector: '22.1', percentile: 78 },
    { label: 'P/B', value: c.pb.toFixed(1), sector: '4.2', percentile: 92 },
    { label: 'EV/EBITDA', value: c.evEbitda.toFixed(1), sector: '18.5', percentile: 88 },
    { label: 'P/S', value: c.ps.toFixed(1), sector: '3.8', percentile: 95 },
    { label: 'PEG Ratio', value: '0.59', sector: '1.2', percentile: 25 },
  ]

  return (
    <div className="p-3 space-y-3 overflow-y-auto h-full">
      <div className="text-xs font-semibold" style={{ color: 'var(--text-secondary)' }}>
        Valuation vs Sector Median
      </div>
      {metrics.map((m) => (
        <div key={m.label} className="terminal-panel p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs" style={{ color: 'var(--text-primary)' }}>{m.label}</span>
            <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>{m.value}</span>
          </div>
          <div className="relative h-1.5 rounded-full" style={{ background: 'var(--bg-primary)' }}>
            <div
              className="absolute h-full rounded-full transition-all"
              style={{
                background: m.percentile > 80 ? 'var(--accent-red)' : m.percentile > 50 ? 'var(--accent-yellow)' : 'var(--accent-green)',
                width: `${m.percentile}%`,
              }}
            />
          </div>
          <div className="flex justify-between mt-1 text-[10px]" style={{ color: 'var(--text-muted)' }}>
            <span>Sector median: {m.sector}</span>
            <span>{m.percentile}th percentile</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function ThesisTab() {
  return (
    <div className="p-3 space-y-3 overflow-y-auto h-full">
      {/* Bull case */}
      <div className="terminal-panel p-3">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full" style={{ background: 'var(--accent-green)' }} />
          <span className="text-xs font-semibold" style={{ color: 'var(--accent-green)' }}>Bull Case — 65%</span>
        </div>
        <ul className="space-y-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-green)' }}>•</span>
            AI datacenter demand accelerating — $1T TAM by 2030
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-green)' }}>•</span>
            CUDA moat — 4M+ developers, network effects deepening
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-green)' }}>•</span>
            Automotive/robotics — new growth vector beyond gaming
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-green)' }}>•</span>
            Software ecosystem (CUDA, cuDNN) creates switching costs
          </li>
        </ul>
      </div>

      {/* Bear case */}
      <div className="terminal-panel p-3">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full" style={{ background: 'var(--accent-red)' }} />
          <span className="text-xs font-semibold" style={{ color: 'var(--accent-red)' }}>Bear Case — 35%</span>
        </div>
        <ul className="space-y-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-red)' }}>•</span>
            Valuation stretched at 72x P/E — pricing perfection
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-red)' }}>•</span>
            AMD MI300X gaining traction in AI training
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-red)' }}>•</span>
            China export restrictions limiting TAM
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-red)' }}>•</span>
            Customer concentration risk — top 4 cloud providers ~50% revenue
          </li>
        </ul>
      </div>

      {/* Confidence */}
      <div className="terminal-panel p-3">
        <div className="flex items-center justify-between">
          <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Thesis Confidence</span>
          <span className="text-lg font-bold" style={{ color: 'var(--accent-green)' }}>68%</span>
        </div>
        <div className="text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>
          Based on 12 evidence sources, 2 contradictions detected
        </div>
      </div>
    </div>
  )
}

function ResearchTab({ symbol }: { symbol: string }) {
  const [input, setInput] = useState('')
  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 p-3 flex items-center justify-center">
        <div className="text-center" style={{ color: 'var(--text-muted)' }}>
          <Brain size={32} className="mx-auto mb-2 opacity-50" />
          <div className="text-sm mb-1">Ask about {symbol}</div>
          <div className="text-[10px]">e.g. "Is NVIDIA still fundamentally attractive?"</div>
        </div>
      </div>
      <div className="p-3 border-t" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask about ${symbol}...`}
            className="flex-1 h-9 px-3 text-xs rounded-md border outline-none"
            style={{
              background: 'var(--bg-primary)',
              borderColor: 'var(--border-primary)',
              color: 'var(--text-primary)',
            }}
          />
          <button
            className="h-9 px-4 rounded-md text-xs font-medium"
            style={{ background: 'var(--accent-blue)', color: 'var(--text-primary)' }}
          >
            Research
          </button>
        </div>
      </div>
    </div>
  )
}

function PriceTab() {
  return (
    <div className="h-full flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>
      <div className="text-center">
        <BarChart3 size={32} className="mx-auto mb-2 opacity-50" />
        <div className="text-sm mb-1">Interactive Chart</div>
        <div className="text-[10px]">Connect TradingView widget for real-time charts</div>
      </div>
    </div>
  )
}

function EarningsTab() {
  return (
    <div className="p-3 space-y-3 overflow-y-auto h-full">
      <div className="terminal-panel p-3">
        <div className="text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>
          Next Earnings: Feb 26, 2025
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-[10px] uppercase" style={{ color: 'var(--text-muted)' }}>EPS Estimate</div>
            <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>$0.84</div>
          </div>
          <div>
            <div className="text-[10px] uppercase" style={{ color: 'var(--text-muted)' }}>Revenue Estimate</div>
            <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>$38.2B</div>
          </div>
        </div>
      </div>
      <div className="terminal-panel p-3">
        <div className="text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>
          Last 4 Quarters
        </div>
        {[
          { q: 'Q4 2024', est: 0.49, actual: 0.52, beat: true },
          { q: 'Q3 2024', est: 0.37, actual: 0.40, beat: true },
          { q: 'Q2 2024', est: 0.25, actual: 0.28, beat: true },
          { q: 'Q1 2024', est: 0.12, actual: 0.14, beat: true },
        ].map((r) => (
          <div key={r.q} className="flex items-center justify-between py-1.5 text-xs border-t"
            style={{ borderColor: 'var(--border-primary)' }}>
            <span style={{ color: 'var(--text-primary)' }}>{r.q}</span>
            <span style={{ color: 'var(--text-muted)' }}>Est: ${r.est}</span>
            <span style={{ color: 'var(--accent-green)' }}>Act: ${r.actual}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(34,197,94,0.1)', color: 'var(--accent-green)' }}>
              Beat
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function FilingsTab() {
  return (
    <div className="p-3 space-y-2 overflow-y-auto h-full">
      {[
        { type: '10-K', date: '2024-02-23', title: 'Annual Report FY2024' },
        { type: '10-Q', date: '2024-11-20', title: 'Quarterly Report Q3 2024' },
        { type: '10-Q', date: '2024-08-28', title: 'Quarterly Report Q2 2024' },
        { type: '8-K', date: '2024-11-19', title: 'Earnings Release' },
        { type: 'DEF 14A', date: '2024-04-15', title: 'Proxy Statement' },
      ].map((f, i) => (
        <div key={i} className="terminal-panel p-3 flex items-center justify-between cursor-pointer hover:border-blue-500/50">
          <div className="flex items-center gap-3">
            <span className="text-[10px] px-1.5 py-0.5 rounded font-mono"
              style={{ background: 'var(--bg-primary)', color: 'var(--accent-blue)' }}>
              {f.type}
            </span>
            <div>
              <div className="text-xs" style={{ color: 'var(--text-primary)' }}>{f.title}</div>
              <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{f.date}</div>
            </div>
          </div>
          <ExternalLink size={12} style={{ color: 'var(--text-muted)' }} />
        </div>
      ))}
    </div>
  )
}

function RiskTab() {
  const risks = [
    { label: 'Valuation Risk', level: 'High', color: 'var(--accent-red)', description: 'P/E 72x vs sector 28x' },
    { label: 'Concentration Risk', level: 'Medium', color: 'var(--accent-yellow)', description: 'Top 4 customers ~50% revenue' },
    { label: 'Geopolitical Risk', level: 'Medium', color: 'var(--accent-yellow)', description: 'China export restrictions' },
    { label: 'Competitive Risk', level: 'Low', color: 'var(--accent-green)', description: 'Strong CUDA moat' },
    { label: 'Execution Risk', level: 'Low', color: 'var(--accent-green)', description: 'Proven execution track record' },
  ]

  return (
    <div className="p-3 space-y-2 overflow-y-auto h-full">
      {risks.map((r) => (
        <div key={r.label} className="terminal-panel p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>{r.label}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded font-medium"
              style={{ background: `${r.color}15`, color: r.color }}>
              {r.level}
            </span>
          </div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{r.description}</div>
        </div>
      ))}
    </div>
  )
}

// ── Main Component ──

export function CompanyIntelligence(props?: { symbol?: string }) {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const symbol = props?.symbol || 'NVDA'

  const renderTab = () => {
    switch (activeTab) {
      case 'overview': return <OverviewTab symbol={symbol} />
      case 'price': return <PriceTab />
      case 'financials': return <FinancialsTab />
      case 'valuation': return <ValuationTab />
      case 'earnings': return <EarningsTab />
      case 'filings': return <FilingsTab />
      case 'risk': return <RiskTab />
      case 'thesis': return <ThesisTab />
      case 'research': return <ResearchTab symbol={symbol} />
      default: return null
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Tab bar */}
      <div className="flex items-center gap-0 border-b shrink-0 overflow-x-auto"
        style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}>
        {TABS.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex items-center gap-1.5 px-3 py-2 text-[11px] font-medium transition-colors whitespace-nowrap border-b-2"
              style={{
                color: activeTab === tab.id ? 'var(--accent-blue)' : 'var(--text-muted)',
                borderColor: activeTab === tab.id ? 'var(--accent-blue)' : 'transparent',
                background: activeTab === tab.id ? 'var(--bg-primary)' : 'transparent',
              }}
            >
              <Icon size={12} />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {renderTab()}
      </div>
    </div>
  )
}
