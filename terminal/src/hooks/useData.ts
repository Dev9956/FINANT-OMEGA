// FININT OMEGA — Data fetching hooks with real backend integration

import { useState, useEffect, useRef } from 'react'
import { market, fundamentals, thesis as thesisApi, anomaly as anomalyApi, estimates } from '../api/client'

// ── Market Data Hook ──

export function useMarketPrices(symbol: string, period = '1mo', interval = '1d') {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    market.getPrices(symbol, period, interval)
      .then(res => { if (!cancelled) { setData(res); setError(null) } })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [symbol, period, interval])

  return { data, loading, error }
}

export function useMarketAnalytics(symbol: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    market.getAnalytics(symbol)
      .then(res => { if (!cancelled) { setData(res); setError(null) } })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [symbol])

  return { data, loading, error }
}

// ── Fundamentals Hook ──

export function useCompanyProfile(symbol: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fundamentals.getProfile(symbol)
      .then(res => { if (!cancelled) { setData(res); setError(null) } })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [symbol])

  return { data, loading, error }
}

export function useFinancialRatios(symbol: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fundamentals.getRatios(symbol)
      .then(res => { if (!cancelled) { setData(res); setError(null) } })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [symbol])

  return { data, loading, error }
}

// ── Thesis Hook ──

export function useThesis(symbol?: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    thesisApi.list(symbol)
      .then(res => { if (!cancelled) { setData(res); setError(null) } })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [symbol])

  return { data, loading, error }
}

// ── Earnings Hook ──

export function useEarnings(symbol: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fundamentals.getEarnings(symbol)
      .then(res => { if (!cancelled) { setData(res); setError(null) } })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [symbol])

  return { data, loading, error }
}

// ── Estimates Hook ──

export function useEstimates(symbol: string) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    estimates.get(symbol)
      .then(res => { if (!cancelled) { setData(res); setError(null) } })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [symbol])

  return { data, loading, error }
}

// ── Anomaly Detection Hook ──

export function useAnomalies() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    anomalyApi.getAnomalies()
      .then((res: any) => { if (!cancelled) { setData(res); setError(null) } })
      .catch((e: any) => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  return { data, loading, error }
}

// ── Polling Hook (for auto-refresh) ──

export function usePolling(callback: () => void, intervalMs: number = 30000) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    const tick = () => savedCallback.current()
    const id = setInterval(tick, intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])
}
