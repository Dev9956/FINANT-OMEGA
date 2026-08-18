// FININT OMEGA — WebSocket hook for real-time data

import { useEffect, useRef, useCallback } from 'react'
import type { WSMessage } from '../types'

type WSHandler = (msg: WSMessage) => void

export function useWebSocket(onMessage: WSHandler) {
  const ws = useRef<WebSocket | null>(null)
  const handlers = useRef(new Set<WSHandler>())
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isConnecting = useRef(false)

  useEffect(() => {
    handlers.current.add(onMessage)
    return () => { handlers.current.delete(onMessage) }
  }, [onMessage])

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN || isConnecting.current) return
    isConnecting.current = true

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const socket = new WebSocket(`${protocol}//${host}/ws`)

    socket.onopen = () => {
      isConnecting.current = false
      // Start heartbeat
      const ping = () => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'ping' }))
          setTimeout(ping, 30000)
        }
      }
      ping()
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage
        handlers.current.forEach(h => h(msg))
      } catch { /* ignore malformed */ }
    }

    socket.onclose = () => {
      isConnecting.current = false
      reconnectTimer.current = setTimeout(connect, 3000) as unknown as ReturnType<typeof setTimeout>
    }

    socket.onerror = () => {
      isConnecting.current = false
      socket.close()
    }

    ws.current = socket
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current as unknown as number)
      ws.current?.close()
    }
  }, [connect])

  const send = useCallback((msg: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(msg))
    }
  }, [])

  return { send }
}
