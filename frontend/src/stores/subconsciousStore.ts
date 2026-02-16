import { create } from 'zustand'

export interface SubconsciousEntry {
  type: 'loud' | 'quiet'
  content: string
  cycle?: number
  timestamp: string
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
