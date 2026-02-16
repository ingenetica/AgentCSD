import { useState, useRef, useEffect } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useSessionStore } from '../stores/sessionStore'
import { Card } from './ui/Card'
import { Badge } from './ui/Badge'

interface ChatPanelProps {
  onSend: (content: string) => void
}

export function ChatPanel({ onSend }: ChatPanelProps) {
  const messages = useChatStore(s => s.messages)
  const sessionId = useSessionStore(s => s.sessionId)
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || !sessionId) return
    useChatStore.getState().addMessage({
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    })
    onSend(text)
    setInput('')
  }

  return (
    <Card
      title="External Dialog"
      headerRight={<Badge color="green">Chat</Badge>}
      className="flex flex-col h-full"
    >
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <p className="text-gray-600 text-sm text-center py-8">
            {sessionId ? 'Send a message to start...' : 'Create or resume a session to begin'}
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
              msg.role === 'user'
                ? 'bg-blue-600/20 border border-blue-800 text-blue-100'
                : 'bg-gray-800 border border-gray-700 text-gray-200'
            }`}>
              <div className="whitespace-pre-wrap break-words">
                {msg.content}
                {msg.streaming && <span className="inline-block w-2 h-4 ml-0.5 bg-gray-400 animate-pulse" />}
              </div>
              <div className="text-[10px] text-gray-500 mt-1">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-gray-800 p-3 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={sessionId ? 'Type a message...' : 'No active session'}
          disabled={!sessionId}
          className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!sessionId || !input.trim()}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>
    </Card>
  )
}
