import { create } from 'zustand'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  streaming?: boolean
}

interface ChatState {
  messages: ChatMessage[]
  addMessage: (msg: ChatMessage) => void
  appendToLastMessage: (chunk: string) => void
  finalizeLastMessage: (content: string) => void
  clear: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  appendToLastMessage: (chunk) => set((s) => {
    const msgs = [...s.messages]
    const last = msgs[msgs.length - 1]
    if (last && last.streaming) {
      msgs[msgs.length - 1] = { ...last, content: last.content + chunk }
    }
    return { messages: msgs }
  }),
  finalizeLastMessage: (content) => set((s) => {
    const msgs = [...s.messages]
    const last = msgs[msgs.length - 1]
    if (last && last.streaming) {
      msgs[msgs.length - 1] = { ...last, content, streaming: false }
    }
    return { messages: msgs }
  }),
  clear: () => set({ messages: [] }),
}))
