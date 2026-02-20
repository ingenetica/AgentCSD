import { create } from 'zustand'

export interface InternalEntry {
  type: 'loud' | 'quiet' | 'input_context'
  content: string
  cycle?: number
  timestamp: string
  internalOnly?: boolean
  // Input context fields
  edUser?: string
  sLoudEntries?: { cycle?: number; content: string }[]
  mood?: string
  criteria?: string
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
