import { create } from 'zustand'
import { useChatStore } from './chatStore'
import { useInternalStore } from './internalStore'
import { useSubconsciousStore } from './subconsciousStore'
import type { Session, Message, MoodAndCriteria } from '../lib/types'

interface SessionState {
  sessionId: string | null
  sessions: Session[]
  error: string | null
  connected: boolean
  setSessionId: (id: string) => void
  setSessions: (sessions: Session[]) => void
  setError: (error: string | null) => void
  setConnected: (connected: boolean) => void
  loadHistory: (history: {
    messages: Message[]
    mood_and_criteria: MoodAndCriteria | null
    cycle: number
  }) => void
  clearSession: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null,
  sessions: [],
  error: null,
  connected: false,
  setSessionId: (id) => set({ sessionId: id, error: null }),
  setSessions: (sessions) => set({ sessions }),
  setError: (error) => set({ error }),
  setConnected: (connected) => set({ connected }),
  loadHistory: (history) => {
    const chatStore = useChatStore.getState()
    const internalStore = useInternalStore.getState()
    const subconsciousStore = useSubconsciousStore.getState()

    chatStore.clear()
    internalStore.clear()
    subconsciousStore.clear()

    for (const msg of history.messages) {
      if (msg.tag === 'ED_user') {
        chatStore.addMessage({ role: 'user', content: msg.content, timestamp: msg.created_at })
      } else if (msg.tag === 'ED_agent') {
        chatStore.addMessage({ role: 'assistant', content: msg.content, timestamp: msg.created_at })
      } else if (msg.tag === 'ID_loud') {
        internalStore.addEntry({ type: 'loud', content: msg.content, cycle: msg.cycle_number ?? undefined, timestamp: msg.created_at })
      } else if (msg.tag === 'ID_quiet') {
        internalStore.addEntry({ type: 'quiet', content: msg.content, cycle: msg.cycle_number ?? undefined, timestamp: msg.created_at })
      } else if (msg.tag === 'S_loud') {
        subconsciousStore.addEntry({ type: 'loud', content: msg.content, cycle: msg.cycle_number ?? undefined, timestamp: msg.created_at })
      } else if (msg.tag === 'S_quiet') {
        subconsciousStore.addEntry({ type: 'quiet', content: msg.content, cycle: msg.cycle_number ?? undefined, timestamp: msg.created_at })
      }
    }

    if (history.mood_and_criteria) {
      subconsciousStore.setMoodAndCriteria(
        history.mood_and_criteria.mood,
        history.mood_and_criteria.criteria,
        history.mood_and_criteria.cycle_number,
      )
    }
    subconsciousStore.setCycle(history.cycle)
  },
  clearSession: () => {
    useChatStore.getState().clear()
    useInternalStore.getState().clear()
    useSubconsciousStore.getState().clear()
    set({ sessionId: null, error: null })
  },
}))
