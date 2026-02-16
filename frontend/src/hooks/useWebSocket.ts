import { useEffect, useRef, useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useInternalStore } from '../stores/internalStore'
import { useSubconsciousStore } from '../stores/subconsciousStore'
import { useSessionStore } from '../stores/sessionStore'
import type { WSMessage } from '../lib/types'

const RECONNECT_DELAY_INITIAL = 1000
const RECONNECT_DELAY_MAX = 30000

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectDelayRef = useRef(RECONNECT_DELAY_INITIAL)
  const messageQueueRef = useRef<string[]>([])
  const intentionalCloseRef = useRef(false)

  const addChat = useChatStore(s => s.addMessage)
  const appendToLastMessage = useChatStore(s => s.appendToLastMessage)
  const finalizeLastMessage = useChatStore(s => s.finalizeLastMessage)
  const addInternal = useInternalStore(s => s.addEntry)
  const addSubconscious = useSubconsciousStore(s => s.addEntry)
  const setMoodAndCriteria = useSubconsciousStore(s => s.setMoodAndCriteria)
  const setCycle = useSubconsciousStore(s => s.setCycle)
  const setRunning = useSubconsciousStore(s => s.setRunning)
  const setSessionId = useSessionStore(s => s.setSessionId)
  const setError = useSessionStore(s => s.setError)
  const setConnected = useSessionStore(s => s.setConnected)
  const loadHistory = useSessionStore(s => s.loadHistory)

  const handleMessage = useCallback((event: MessageEvent) => {
    const msg: WSMessage = JSON.parse(event.data)

    switch (msg.type) {
      case 'ed_agent':
        addChat({ role: 'assistant', content: msg.content || '', timestamp: msg.timestamp || '' })
        break
      case 'ed_agent_chunk': {
        const chatState = useChatStore.getState()
        const last = chatState.messages[chatState.messages.length - 1]
        if (last && last.streaming) {
          appendToLastMessage(msg.content || '')
        } else {
          addChat({ role: 'assistant', content: msg.content || '', timestamp: msg.timestamp || '', streaming: true })
        }
        break
      }
      case 'ed_agent_done':
        finalizeLastMessage(msg.content || '')
        break
      case 'id_loud':
        addInternal({ type: 'loud', content: msg.content || '', cycle: msg.cycle, timestamp: msg.timestamp || '' })
        break
      case 'id_quiet':
        addInternal({ type: 'quiet', content: msg.content || '', cycle: msg.cycle, timestamp: msg.timestamp || '' })
        break
      case 's_loud':
        addSubconscious({ type: 'loud', content: msg.content || '', cycle: msg.cycle, timestamp: msg.timestamp || '' })
        break
      case 's_quiet':
        addSubconscious({ type: 'quiet', content: msg.content || '', cycle: msg.cycle, timestamp: msg.timestamp || '' })
        break
      case 'm_and_c':
        setMoodAndCriteria(msg.mood || '', msg.criteria || '', msg.cycle)
        break
      case 'status':
        setRunning(msg.subconscious_running ?? false)
        if (msg.cycle !== undefined) setCycle(msg.cycle)
        break
      case 'session_created':
        setSessionId(msg.session_id || '')
        break
      case 'session_resumed':
        setSessionId(msg.session_id || '')
        if (msg.history) loadHistory(msg.history)
        break
      case 'error':
        setError(msg.message || 'Unknown error')
        break
    }
  }, [addChat, appendToLastMessage, finalizeLastMessage, addInternal, addSubconscious,
      setMoodAndCriteria, setCycle, setRunning, setSessionId, setError, setConnected, loadHistory])

  const connectRef = useRef<() => void>(() => {})

  const scheduleReconnect = useCallback(() => {
    if (intentionalCloseRef.current) return
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)

    const delay = reconnectDelayRef.current
    reconnectTimeoutRef.current = setTimeout(() => {
      connectRef.current()
    }, delay)
    reconnectDelayRef.current = Math.min(delay * 2, RECONNECT_DELAY_MAX)
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setError(null)
      reconnectDelayRef.current = RECONNECT_DELAY_INITIAL

      // Flush queued messages
      while (messageQueueRef.current.length > 0) {
        const queued = messageQueueRef.current.shift()!
        ws.send(queued)
      }

      // Auto-resume session if one was active
      const sessionId = useSessionStore.getState().sessionId
      if (sessionId) {
        ws.send(JSON.stringify({ type: 'resume_session', session_id: sessionId }))
      }
    }

    ws.onmessage = handleMessage

    ws.onclose = () => {
      setConnected(false)
      if (!intentionalCloseRef.current) {
        scheduleReconnect()
      }
    }

    ws.onerror = () => {
      // onclose will fire after onerror, so reconnect is handled there
    }
  }, [handleMessage, setConnected, setError, scheduleReconnect])

  connectRef.current = connect

  useEffect(() => {
    intentionalCloseRef.current = false
    connect()

    return () => {
      intentionalCloseRef.current = true
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [connect])

  const send = useCallback((data: Record<string, unknown>) => {
    const payload = JSON.stringify(data)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(payload)
    } else {
      messageQueueRef.current.push(payload)
    }
  }, [])

  return { send }
}
