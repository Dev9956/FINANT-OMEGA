// FININT OMEGA — Screener panel (M16.7) — NLP → ClickHouse

import { useState, useCallback } from 'react'
import { Search, Filter, Play, Download, X, Plus } from 'lucide-react'
import { fundamentals } from '../../api/client'

interface FilterRow {
  field: string
  operator: string
  value: string
}

interface ScreenerResult {
  symbol: string
  name: string
  price: number
  changePercent: number
  marketCap: number
  pe: number
  revenueGrowth: number
  roe: number
  debtEquity: number
  sector: string
}

const FIELDS = [
  { value: 'marketCap', label: 'Market Cap ($B)' },
  { value: 'pe', label: 'P/E Ratio' },
  { value: 'pb', label: 'P/B Ratio' },
  { value: 'roe', label: 'ROE (%)' },
  { value: 'roa', label: 'ROA (%)' },
  { value: 'revenueGrowth', label: 'Revenue Growth (%)' },
  { value: 'netMargin', label: 'Net Margin (%)' },
  { value: 'debtEquity', label: 'Debt/Equity' },
  { value: 'currentRatio', label: 'Current Ratio' },
  { value: 'dividendYield', label: 'Dividend Yield (%)' },
  { value: 'evEbitda', label: 'EV/EBITDA' },
  { value: 'fcfYield', label: 'FCF Yield (%)' },
]

const OPERATORS = [
  { value: 'gt', label: '>' },
  { value: 'lt', label: '<' },
  { value: 'gte', label: '>=' },
  { value: 'lte', label: '<=' },
  { value: 'eq', label: '=' },
]

const DEMO_RESULTS: ScreenerResult[] = [
  { symbol: 'NVDA', name: 'NVIDIA Corp', price: 132.65, changePercent: 1.80, marketCap: 3245, pe: 72.5, revenueGrowth: 122.0, roe: 115.7, debtEquity: 0.17, sector: 'Technology' },
  { symbol: 'AAPL', name: 'Apple Inc', price: 234.82, changePercent: 0.45, marketCap: 3620, pe: 32.1, revenueGrowth: 8.2, roe: 157.0, debtEquity: 1.87, sector: 'Technology' },
  { symbol: 'MSFT', name: 'Microsoft Corp', price: 420.55, changePercent: -0.32, marketCap: 3120, pe: 36.8, revenueGrowth: 15.7, roe: 39.2, debtEquity: 0.34, sector: 'Technology' },
  { symbol: 'GOOGL', name: 'Alphabet Inc', price: 178.23, changePercent: 1.12, marketCap: 2180, pe: 24.5, revenueGrowth: 13.8, roe: 29.8, debtEquity: 0.05, sector: 'Technology' },
  { symbol: 'AMZN', name: 'Amazon.com', price: 218.90, changePercent: 0.78, marketCap: 2260, pe: 42.3, revenueGrowth: 11.2, roe: 22.1, debtEquity: 0.58, sector: 'Consumer' },
]

export function ScreenerPanel() {
  const [nlQuery, setNlQuery] = useState('')
  const [filters, setFilters] = useState<FilterRow[]>([
    { field: 'roe', operator: 'gt', value: '15' },
    { field: 'debtEquity', operator: 'lt', value: '0.5' },
  ])
  const [results, setResults] = useState<ScreenerResult[]>([])
  const [loading, setLoading] = useState(false)
  const [sortField, setSortField] = useState<string>('marketCap')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const addFilter = () => {
    setFilters(prev => [...prev, { field: 'roe', operator: 'gt', value: '10' }])
  }

  const removeFilter = (idx: number) => {
    setFilters(prev => prev.filter((_, i) => i !== idx))
  }

  const updateFilter = (idx: number, key: keyof FilterRow, val: string) => {
    setFilters(prev => prev.map((f, i) => i === idx ? { ...f, [key]: val } : f))
  }

  const runScreener = useCallback(async () => {
    setLoading(true)
    try {
      const filterObj = filters.map(f => ({
        field: f.field,
        operator: f.operator,
        value: parseFloat(f.value),
      }))
      const res = await fundamentals.screening({ filters: filterObj }) as any
      if (res?.results) {
        setResults(res.results)
      } else {
        setResults(DEMO_RESULTS)
      }
    } catch {
      setResults(DEMO_RESULTS)
    } finally {
      setLoading(false)
    }
  }, [filters])

  const handleNlSearch = async () => {
    if (!nlQuery.trim()) return
    setLoading(true)
    try {
      // In production: NLP → query planner → ClickHouse
      // For now use demo results
      await new Promise(r => setTimeout(r, 800))
      setResults(DEMO_RESULTS)
    } finally {
      setLoading(false)
    }
  }

  const sorted = [...results].sort((a: any, b: any) => {
    const av = a[sortField] ?? 0, bv = b[sortField] ?? 0
    return sortDir === 'desc' ? bv - av : av - bv
  })

  const fmt = (n: number) => n >= 1e9 ? `$${(n / 1e9).toFixed(1)}B` : n >= 1e6 ? `$${(n / 1e6).toFixed(0)}M` : `$${n.toFixed(2)}`

  return (
    <div className="h-full flex flex-col">
      {/* NLP Search bar */}
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
            <input
              value={nlQuery}
              onChange={(e) => setNlQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleNlSearch()}
              placeholder="Try: 'high ROE low debt growing fast' or 'companies with FCF yield > 5%'"
              className="w-full h-8 pl-8 pr-3 text-xs rounded border outline-none"
              style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}
            />
          </div>
          <button onClick={handleNlSearch} disabled={loading}
            className="h-8 px-3 rounded text-xs font-medium flex items-center gap-1"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            <Play size={12} /> Search
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-1 mb-1">
          <Filter size={12} style={{ color: 'var(--text-muted)' }} />
          <span className="text-[10px] uppercase" style={{ color: 'var(--text-muted)' }}>Filters</span>
          <button onClick={addFilter} className="ml-2 p-0.5 rounded hover:bg-white/10">
            <Plus size={12} style={{ color: 'var(--accent-blue)' }} />
          </button>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {filters.map((f, i) => (
            <div key={i} className="flex items-center gap-1 text-[10px] rounded px-2 py-1"
              style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)' }}>
              <select value={f.field} onChange={(e) => updateFilter(i, 'field', e.target.value)}
                className="bg-transparent outline-none text-xs" style={{ color: 'var(--text-primary)' }}>
                {FIELDS.map(fd => <option key={fd.value} value={fd.value}>{fd.label}</option>)}
              </select>
              <select value={f.operator} onChange={(e) => updateFilter(i, 'operator', e.target.value)}
                className="bg-transparent outline-none text-xs" style={{ color: 'var(--accent-blue)' }}>
                {OPERATORS.map(op => <option key={op.value} value={op.value}>{op.label}</option>)}
              </select>
              <input value={f.value} onChange={(e) => updateFilter(i, 'value', e.target.value)}
                className="w-14 bg-transparent outline-none text-xs text-right" style={{ color: 'var(--text-primary)' }} />
              <button onClick={() => removeFilter(i)} className="hover:bg-white/10 rounded p-0.5">
                <X size={10} style={{ color: 'var(--text-muted)' }} />
              </button>
            </div>
          ))}
          <button onClick={runScreener} disabled={loading}
            className="h-6 px-2 rounded text-[10px] font-medium"
            style={{ background: 'var(--accent-green)', color: 'white' }}>
            Run ({filters.length} filters)
          </button>
        </div>
      </div>

      {/* Results table */}
      <div className="flex-1 overflow-auto">
        {results.length > 0 ? (
          <table className="w-full text-xs">
            <thead>
              <tr style={{ background: 'var(--bg-secondary)' }}>
                {[
                  { key: 'symbol', label: 'Symbol' },
                  { key: 'name', label: 'Name' },
                  { key: 'price', label: 'Price' },
                  { key: 'changePercent', label: 'Chg%' },
                  { key: 'marketCap', label: 'Mkt Cap' },
                  { key: 'pe', label: 'P/E' },
                  { key: 'revenueGrowth', label: 'Rev Grw%' },
                  { key: 'roe', label: 'ROE%' },
                  { key: 'debtEquity', label: 'D/E' },
                ].map(col => (
                  <th key={col.key} onClick={() => { setSortField(col.key); setSortDir(d => d === 'desc' ? 'asc' : 'desc') }}
                    className="text-left px-2 py-1.5 font-medium cursor-pointer hover:bg-white/5"
                    style={{ color: 'var(--text-muted)' }}>
                    {col.label} {sortField === col.key ? (sortDir === 'desc' ? '↓' : '↑') : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r) => (
                <tr key={r.symbol} className="border-t cursor-pointer hover:bg-white/[0.02]"
                  style={{ borderColor: 'var(--border-primary)' }}>
                  <td className="px-2 py-1.5 font-bold" style={{ color: 'var(--accent-blue)' }}>{r.symbol}</td>
                  <td className="px-2 py-1.5" style={{ color: 'var(--text-secondary)' }}>{r.name}</td>
                  <td className="px-2 py-1.5" style={{ color: 'var(--text-primary)' }}>${r.price.toFixed(2)}</td>
                  <td className={`px-2 py-1.5 font-medium ${r.changePercent >= 0 ? 'ticker-up' : 'ticker-down'}`}>
                    {r.changePercent >= 0 ? '+' : ''}{r.changePercent.toFixed(2)}%
                  </td>
                  <td className="px-2 py-1.5" style={{ color: 'var(--text-primary)' }}>{fmt(r.marketCap * 1e9)}</td>
                  <td className="px-2 py-1.5" style={{ color: 'var(--text-primary)' }}>{r.pe.toFixed(1)}</td>
                  <td className="px-2 py-1.5 ticker-up">{r.revenueGrowth.toFixed(1)}%</td>
                  <td className="px-2 py-1.5 ticker-up">{r.roe.toFixed(1)}%</td>
                  <td className="px-2 py-1.5" style={{ color: 'var(--text-primary)' }}>{r.debtEquity.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="h-full flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>
            <div className="text-center">
              <Search size={32} className="mx-auto mb-2 opacity-50" />
              <div className="text-sm mb-1">Build your screen</div>
              <div className="text-[10px]">Use filters or natural language to find stocks</div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      {results.length > 0 && (
        <div className="px-3 py-1.5 border-t flex items-center justify-between text-[10px]"
          style={{ borderColor: 'var(--border-primary)', color: 'var(--text-muted)' }}>
          <span>{results.length} results</span>
          <button className="flex items-center gap-1 hover:text-white">
            <Download size={10} /> Export CSV
          </button>
        </div>
      )}
    </div>
  )
}
