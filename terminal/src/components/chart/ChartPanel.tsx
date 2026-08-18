// FININT OMEGA — TradingView-style chart using lightweight-charts

import { useEffect, useRef, useState, useCallback } from 'react'
import { createChart, CandlestickSeries, HistogramSeries } from 'lightweight-charts'
import { market } from '../../api/client'

interface ChartProps {
  symbol?: string
  height?: number
}

const TIMEFRAMES: { label: string; period: string; interval: string }[] = [
  { label: '1D', period: '1d', interval: '5m' },
  { label: '1W', period: '5d', interval: '15m' },
  { label: '1M', period: '1mo', interval: '1d' },
  { label: '3M', period: '3mo', interval: '1d' },
  { label: '1Y', period: '1y', interval: '1wk' },
]

export function ChartPanel({ symbol: initialSymbol = 'SPY', height = 400 }: ChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<any>(null)
  const candleSeries = useRef<any>(null)
  const volumeSeries = useRef<any>(null)
  const disposedRef = useRef(false)
  const [symbol, setSymbol] = useState(initialSymbol)
  const [symbolInput, setSymbolInput] = useState(initialSymbol)
  const [activeTimeframe, setActiveTimeframe] = useState('1M')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPrice, setCurrentPrice] = useState<number | null>(null)
  const [priceChange, setPriceChange] = useState({ change: 0, changePercent: 0 })

  const handleSymbolSubmit = () => {
    const s = symbolInput.trim().toUpperCase()
    if (s && s !== symbol) {
      setSymbol(s)
    }
  }

  useEffect(() => {
    if (!chartRef.current) return
    disposedRef.current = false

    if (chartInstance.current) {
      try { chartInstance.current.remove() } catch {}
      chartInstance.current = null
    }

    const chart = createChart(chartRef.current, {
      layout: {
        background: { color: '#0a0e17' },
        textColor: '#8b949e',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: '#1e2736' },
        horzLines: { color: '#1e2736' },
      },
      crosshair: {
        mode: 0,
        vertLine: { color: '#3b82f6', width: 1, style: 2 },
        horzLine: { color: '#3b82f6', width: 1, style: 2 },
      },
      rightPriceScale: { borderColor: '#1e2736' },
      timeScale: { borderColor: '#1e2736', timeVisible: true, secondsVisible: false },
      width: chartRef.current.clientWidth,
      height,
    })

    const candle = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e', downColor: '#ef4444',
      borderUpColor: '#22c55e', borderDownColor: '#ef4444',
      wickUpColor: '#22c55e', wickDownColor: '#ef4444',
    })

    const volume = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })

    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } })

    chartInstance.current = chart
    candleSeries.current = candle
    volumeSeries.current = volume

    const handleResize = () => {
      if (chartRef.current && chartInstance.current && !disposedRef.current) {
        chartInstance.current.applyOptions({ width: chartRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      disposedRef.current = true
      window.removeEventListener('resize', handleResize)
      try { chart.remove() } catch {}
      chartInstance.current = null
      candleSeries.current = null
      volumeSeries.current = null
    }
  }, [height])

  const fetchData = useCallback(async (tf: string) => {
    if (!candleSeries.current || !volumeSeries.current) return
    setLoading(true)

    const tfConfig = TIMEFRAMES.find(t => t.label === tf) || TIMEFRAMES[2]

    try {
      const res: any = await market.getPrices(symbol, tfConfig.period, tfConfig.interval)
      const data = res?.data || res

      if (data?.ohlc && Array.isArray(data.ohlc)) {
        const candles = data.ohlc.map((d: any) => ({
          time: (d.date || d.time || d.timestamp) as any,
          open: d.open, high: d.high, low: d.low, close: d.close,
        }))
        if (!disposedRef.current) candleSeries.current.setData(candles)

        if (data.ohlc.length > 0) {
          const last = data.ohlc[data.ohlc.length - 1]
          setCurrentPrice(last.close)
          if (data.ohlc.length >= 2) {
            const prev = data.ohlc[data.ohlc.length - 2]
            setPriceChange({
              change: last.close - prev.close,
              changePercent: ((last.close - prev.close) / prev.close) * 100,
            })
          }
        }

        const volumes = data.ohlc.map((d: any) => ({
          time: (d.date || d.time || d.timestamp) as any,
          value: d.volume || 0,
          color: d.close >= d.open ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)',
        }))
        if (!disposedRef.current) volumeSeries.current.setData(volumes)
      } else if (Array.isArray(data)) {
        const candles = data.map((d: any) => ({
          time: d.date || d.time || d.timestamp,
          open: d.open, high: d.high, low: d.low, close: d.close,
        }))
        if (!disposedRef.current) {
          candleSeries.current.setData(candles)
          volumeSeries.current.setData(data.map((d: any) => ({
            time: d.date || d.time || d.timestamp,
            value: d.volume || 0,
            color: d.close >= d.open ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)',
          })))
        }
        if (data.length > 0) setCurrentPrice(data[data.length - 1].close)
      }
    } catch (err: any) {
      if (disposedRef.current) return
      setError(err.message || `Failed to load market data for ${symbol}`)
    } finally {
      setLoading(false)
    }
  }, [symbol])

  useEffect(() => {
    const timer = setTimeout(() => fetchData(activeTimeframe), 100)
    // Auto refresh every 10 seconds for real-time market data ticks
    const interval = setInterval(() => fetchData(activeTimeframe), 10000)
    return () => {
      clearTimeout(timer)
      clearInterval(interval)
    }
  }, [activeTimeframe, fetchData])

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-3 py-1.5 border-b shrink-0 gap-2 overflow-x-auto"
        style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2">
          {/* Symbol input */}
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={symbolInput}
              onChange={(e) => setSymbolInput(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleSymbolSubmit()}
              className="w-16 h-6 px-1.5 text-xs font-bold uppercase rounded border outline-none"
              style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--accent-blue)' }}
            />
            <button onClick={handleSymbolSubmit}
              className="h-6 px-1.5 rounded text-[10px] font-medium border"
              style={{ borderColor: 'var(--border-primary)', color: 'var(--text-secondary)' }}>
              LOAD
            </button>
          </div>

          {/* Quick symbol chips */}
          <div className="hidden sm:flex items-center gap-1">
            {['SPY', 'NVDA', 'AAPL', 'TSLA', 'MSFT'].map(s => (
              <button key={s} onClick={() => { setSymbol(s); setSymbolInput(s) }}
                className="px-1.5 py-0.5 text-[9px] rounded font-medium"
                style={{
                  background: symbol === s ? 'var(--bg-tertiary)' : 'transparent',
                  color: symbol === s ? 'var(--accent-blue)' : 'var(--text-muted)',
                }}>
                {s}
              </button>
            ))}
          </div>

          {currentPrice && (
            <div className="flex items-center gap-1.5 ml-1">
              <span className="text-xs font-mono font-bold" style={{ color: 'var(--text-primary)' }}>
                ${currentPrice.toFixed(2)}
              </span>
              <span className={`text-[10px] font-mono ${priceChange.change >= 0 ? 'ticker-up' : 'ticker-down'}`}>
                {priceChange.change >= 0 ? '+' : ''}{priceChange.change.toFixed(2)} ({priceChange.changePercent.toFixed(2)}%)
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-0.5">
          {TIMEFRAMES.map(tf => (
            <button key={tf.label} onClick={() => setActiveTimeframe(tf.label)}
              className="px-2 py-0.5 text-[10px] rounded transition-colors font-medium"
              style={{
                background: activeTimeframe === tf.label ? 'var(--accent-blue)' : 'transparent',
                color: activeTimeframe === tf.label ? 'white' : 'var(--text-muted)',
              }}>
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10" style={{ background: 'rgba(10,14,23,0.5)' }}>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Loading live chart...</div>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center z-10 p-4" style={{ background: 'rgba(10,14,23,0.85)' }}>
            <div className="text-xs text-center p-3 rounded border" style={{ background: 'var(--accent-red)15', borderColor: 'var(--accent-red)', color: 'var(--accent-red)' }}>
              {error}
            </div>
          </div>
        )}
        <div ref={chartRef} className="w-full h-full" />
      </div>
    </div>
  )
}
