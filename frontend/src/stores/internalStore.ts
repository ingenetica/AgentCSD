import { create } from 'zustand'

export interface InternalEntry {
  type: 'loud' | 'quiet'
  content: string
  cycle?: number
  timestamp: string
  internalOnly?: boolean
}

interface InternalState {
  entries: InternalEntry[]
  addEntry: (entry: InternalEntry) => void
  clear: () => void
}

export const useInternalStore = create<InternalState>((set) => ({
  entries: [],
  addEntry: (entry) => set((s) => ({ entries: [...s.entries, entry] })),
  clear: () => set({ entries: [] }),
}))
