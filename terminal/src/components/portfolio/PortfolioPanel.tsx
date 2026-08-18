// FININT OMEGA — Portfolio — wired to real backend API (portfolio CRUD + market prices)

import { useState, useEffect, useCallback } from 'react'
import { Briefcase, RefreshCw, Loader2, Plus, Trash2, TrendingUp, TrendingDown } from 'lucide-react'
import { portfolio, market } from '../../api/client'

interface Position {
  position_id: string
  symbol: string
  quantity: number
  avg_cost: number
  side: string
  cost_basis: number
  current_price?: number
  market_value?: number
  pnl?: number
  pnl_pct?: number
  created_at: string
}

export function PortfolioPanel() {
  const [positions, setPositions] = useState<Position[]>([])
  const [loading, setLoading] = useState(false)
  const [adding, setAdding] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [form, setForm] = useState({ symbol: 'NVDA', quantity: 100, avg_cost: 120 })

  const fetchPositions = useCallback(async () => {
    setLoading(true)
    try {
      const data = await portfolio.listPositions() as any
      const pos = data.positions || []
      // Fetch current prices for each position
      const withPrices = await Promise.all(pos.map(async (p: Position) => {
        try {
          const priceData = await market.getPrices(p.symbol, '1d', '1d') as any
          const prices = priceData.prices || []
          const lastPrice = prices.length > 0 ? prices[prices.length - 1].close : p.avg_cost
          const mv = p.quantity * lastPrice
          const pnl = (lastPrice - p.avg_cost) * p.quantity
          const pnlPct = p.avg_cost > 0 ? (lastPrice - p.avg_cost) / p.avg_cost : 0
          return { ...p, current_price: lastPrice, market_value: mv, pnl, pnl_pct: pnlPct }
        } catch {
          return { ...p, current_price: p.avg_cost, market_value: p.cost_basis, pnl: 0, pnl_pct: 0 }
        }
      }))
      setPositions(withPrices)
    } catch {} finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchPositions() }, [fetchPositions])

  const handleAdd = async () => {
    if (!form.symbol.trim()) return
    setAdding(true)
    try {
      await portfolio.addPosition({
        symbol: form.symbol.toUpperCase(),
        quantity: form.quantity,
        avg_cost: form.avg_cost,
        side: 'long',
      })
      setForm({ symbol: 'NVDA', quantity: 100, avg_cost: 120 })
      await fetchPositions()
    } catch {} finally { setAdding(false) }
  }

  const handleDelete = async (id: string) => {
    try {
      await portfolio.deletePosition(id)
      await fetchPositions()
    } catch {}
  }

  const handleRefreshPrices = async () => {
    setRefreshing(true)
    await fetchPositions()
    setRefreshing(false)
  }

  const totalCost = positions.reduce((sum, p) => sum + p.cost_basis, 0)
  const totalMV = positions.reduce((sum, p) => sum + (p.market_value || p.cost_basis), 0)
  const totalPnL = totalMV - totalCost
  const totalPnLPct = totalCost > 0 ? totalPnL / totalCost : 0

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2 mb-2">
          <Briefcase size={14} style={{ color: 'var(--accent-blue)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Portfolio</span>
          <div className="flex-1" />
          <button onClick={handleRefreshPrices} disabled={refreshing}
            className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-3 gap-1.5 mb-2">
          <div className="p-1.5 rounded text-center" style={{ background: 'var(--bg-primary)' }}>
            <div className="text-[8px] uppercase" style={{ color: 'var(--text-muted)' }}>Market Value</div>
            <div className="text-[11px] font-bold font-mono" style={{ color: 'var(--text-primary)' }}>
              ${totalMV.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </div>
          <div className="p-1.5 rounded text-center" style={{ background: 'var(--bg-primary)' }}>
            <div className="text-[8px] uppercase" style={{ color: 'var(--text-muted)' }}>P&L</div>
            <div className="text-[11px] font-bold font-mono" style={{ color: totalPnL >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {totalPnL >= 0 ? '+' : ''}{totalPnL.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </div>
          <div className="p-1.5 rounded text-center" style={{ background: 'var(--bg-primary)' }}>
            <div className="text-[8px] uppercase" style={{ color: 'var(--text-muted)' }}>Return</div>
            <div className="text-[11px] font-bold font-mono" style={{ color: totalPnLPct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {totalPnLPct >= 0 ? '+' : ''}{(totalPnLPct * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Add form */}
        <div className="flex items-center gap-1">
          <input value={form.symbol} onChange={e => setForm(f => ({ ...f, symbol: e.target.value }))}
            placeholder="SYM" className="w-14 h-6 px-1 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <input type="number" value={form.quantity} onChange={e => setForm(f => ({ ...f, quantity: +e.target.value }))}
            placeholder="Qty" className="w-14 h-6 px-1 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <input type="number" step="0.01" value={form.avg_cost} onChange={e => setForm(f => ({ ...f, avg_cost: +e.target.value }))}
            placeholder="Cost" className="w-16 h-6 px-1 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }} />
          <button onClick={handleAdd} disabled={adding}
            className="h-6 px-2 rounded text-[10px] font-medium flex items-center gap-1"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {adding ? <Loader2 size={8} className="animate-spin" /> : <Plus size={8} />}
          </button>
        </div>
      </div>

      {/* Positions */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin mr-2" /> Loading...
          </div>
        ) : positions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <Briefcase size={24} className="mb-2 opacity-30" />
            <div className="text-xs">No positions yet</div>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: 'var(--border-primary)' }}>
            {positions.map(p => (
              <div key={p.position_id} className="px-2 py-1.5 flex items-center gap-2 hover:bg-white/[0.02]">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-bold" style={{ color: 'var(--text-primary)' }}>{p.symbol}</span>
                    <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>{p.quantity} shares</span>
                  </div>
                  <div className="flex items-center gap-2 text-[9px]">
                    <span style={{ color: 'var(--text-muted)' }}>Cost: ${p.avg_cost.toFixed(2)}</span>
                    <span style={{ color: 'var(--text-muted)' }}>Price: ${(p.current_price || 0).toFixed(2)}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-mono" style={{ color: 'var(--text-primary)' }}>
                    ${(p.market_value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                  <div className="flex items-center gap-0.5 text-[9px] font-mono"
                    style={{ color: (p.pnl || 0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                    {(p.pnl || 0) >= 0 ? <TrendingUp size={8} /> : <TrendingDown size={8} />}
                    {((p.pnl_pct || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                <button onClick={() => handleDelete(p.position_id)}
                  className="p-0.5 rounded hover:bg-white/10" style={{ color: 'var(--text-muted)' }}>
                  <Trash2 size={10} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
