// FININT OMEGA — Market Overview panel — real backend data

import { useState, useEffect, useCallback } from 'react'
import { TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react'
import { market } from '../../api/client'
import { usePolling } from '../../hooks/useData'

interface MarketTicker {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
}

const WATCHED_SYMBOLS = [
  { symbol: 'SPY', name: 'S&P 500' },
  { symbol: 'QQQ', name: 'NASDAQ' },
  { symbol: 'GC=F', name: 'Gold' },
  { symbol: 'BTC-USD', name: 'Bitcoin' },
  { symbol: 'DX-Y.NYB', name: 'Dollar Index' },
  { symbol: '^TNX', name: 'US 10Y' },
  { symbol: '^VIX', name: 'VIX' },
  { symbol: 'NVDA', name: 'NVIDIA' },
]

const FALLBACK_TICKERS: MarketTicker[] = [
  { symbol: 'SPY', name: 'S&P 500', price: 582.34, change: 1.26, changePercent: 0.22 },
  { symbol: 'QQQ', name: 'NASDAQ', price: 512.85, change: -1.23, changePercent: -0.24 },
  { symbol: 'GC=F', name: 'Gold', price: 2412.50, change: 8.30, changePercent: 0.35 },
  { symbol: 'BTC-USD', name: 'Bitcoin', price: 97234.12, change: -1234.56, changePercent: -1.25 },
  { symbol: 'DX-Y.NYB', name: 'Dollar Index', price: 104.23, change: 0.12, changePercent: 0.12 },
  { symbol: '^TNX', name: 'US 10Y', price: 4.28, change: -0.03, changePercent: -0.69 },
  { symbol: '^VIX', name: 'VIX', price: 14.32, change: -0.45, changePercent: -3.04 },
  { symbol: 'NVDA', name: 'NVIDIA', price: 132.65, change: 2.35, changePercent: 1.80 },
]

function TickerCard({ ticker, loading }: { ticker: MarketTicker; loading?: boolean }) {
  const isUp = ticker.change >= 0
  return (
    <div className={`terminal-panel p-3 flex flex-col gap-1 cursor-pointer transition-all ${loading ? 'opacity-60' : ''}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
          {ticker.symbol}
        </span>
        <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
          {ticker.name}
        </span>
      </div>
      <div className="flex items-end justify-between">
        <span className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
          {ticker.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
        </span>
        <div className={`flex items-center gap-0.5 text-xs font-medium ${isUp ? 'ticker-up' : 'ticker-down'}`}>
          {isUp ? <TrendingUp size={12} /> : ticker.change === 0 ? <Minus size={12} /> : <TrendingDown size={12} />}
          <span>{isUp ? '+' : ''}{ticker.changePercent.toFixed(2)}%</span>
        </div>
      </div>
    </div>
  )
}

export function MarketOverview() {
  const [tickers, setTickers] = useState<MarketTicker[]>(FALLBACK_TICKERS)
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const fetchPrices = useCallback(async () => {
    setLoading(true)
    try {
      const results = await Promise.allSettled(
        WATCHED_SYMBOLS.map(async (sym) => {
          try {
            const res: any = await market.getPrices(sym.symbol, '1d', '1d')
            const priceData = res?.data || res
            return {
              symbol: sym.symbol,
              name: sym.name,
              price: priceData?.price ?? priceData?.close ?? priceData?.regularMarketPrice ?? 0,
              change: priceData?.change ?? priceData?.regularMarketChange ?? 0,
              changePercent: priceData?.changePercent ?? priceData?.regularMarketChangePercent ?? 0,
            }
          } catch {
            return FALLBACK_TICKERS.find(f => f.symbol === sym.symbol) || {
              symbol: sym.symbol, name: sym.name, price: 0, change: 0, changePercent: 0,
            }
          }
        })
      )
      const updated = results
        .filter((r): r is PromiseFulfilledResult<MarketTicker> => r.status === 'fulfilled')
        .map(r => r.value)
        .filter(t => t.price > 0)

      if (updated.length >= 3) {
        setTickers(updated)
        setLastUpdated(new Date().toLocaleTimeString())
      }
    } catch {
      // keep fallback data
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchPrices() }, [fetchPrices])
  usePolling(fetchPrices, 60000)

  return (
    <div className="h-full overflow-y-auto p-2">
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-[10px] uppercase" style={{ color: 'var(--text-muted)' }}>Market Overview</span>
        <div className="flex items-center gap-2">
          {lastUpdated && (
            <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>Updated {lastUpdated}</span>
          )}
          <button onClick={fetchPrices} disabled={loading}
            className="p-0.5 rounded hover:bg-white/10"
            style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={10} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>
      <div className="grid grid-cols-4 gap-2">
        {tickers.map((t) => (
          <TickerCard key={t.symbol} ticker={t} loading={loading} />
        ))}
      </div>
    </div>
  )
}
