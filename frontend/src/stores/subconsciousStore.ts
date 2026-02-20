import { create } from 'zustand'

export interface SubconsciousEntry {
  type: 'loud' | 'quiet' | 'input_context'
  content: string
  cycle?: number
  timestamp: string
  // Input context fields
  edUser?: string
  edAgent?: string
  idLoud?: string
  idQuiet?: string
}

interface SubconsciousState {
  entries: SubconsciousEntry[]
  mood: string
  criteria: string
  cycle: number
  running: boolean
  addEntry: (entry: SubconsciousEntry) => void
  setMoodAndCriteria: (mood: string, criteria: string, cycle?: number) => void
  setCycle: (cycle: number) => void
  setRunning: (running: boolean) => void
  clear: () => void
}

export const useSubconsciousStore = create<SubconsciousState>((set) => ({
  entries: [],
  mood: '',
  criteria: '',
  cycle: 0,
  running: false,
  addEntry: (entry) => set((s) => ({ entries: [...s.entries, entry] })),
  setMoodAndCriteria: (mood, criteria, cycle) =>
    set((s) => ({ mood, criteria, ...(cycle !== undefined ? { cycle } : {}) })),
  setCycle: (cycle) => set({ cycle }),
  setRunning: (running) => set({ running }),
  clear: () => set({ entries: [], mood: '', criteria: '', cycle: 0, running: false }),
}))
