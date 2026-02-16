import { useState, useEffect } from 'react'
import { useSessionStore } from '../stores/sessionStore'
import { useSubconsciousStore } from '../stores/subconsciousStore'
import { api } from '../lib/api'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Modal } from './ui/Modal'
import type { Session, Persona } from '../lib/types'

interface SidebarProps {
  onCreateSession: (name: string, persona: string) => void
  onResumeSession: (sessionId: string) => void
  onPause: () => void
  onResume: () => void
  onOpenPersonaEditor: () => void
  onOpenConfig: () => void
}

export function Sidebar({
  onCreateSession, onResumeSession, onPause, onResume,
  onOpenPersonaEditor, onOpenConfig,
}: SidebarProps) {
  const sessionId = useSessionStore(s => s.sessionId)
  const connected = useSessionStore(s => s.connected)
  const running = useSubconsciousStore(s => s.running)
  const error = useSessionStore(s => s.error)

  const [sessions, setSessions] = useState<Session[]>([])
  const [personas, setPersonas] = useState<Persona[]>([])
  const [showNew, setShowNew] = useState(false)
  const [newName, setNewName] = useState('')
  const [selectedPersona, setSelectedPersona] = useState('default.md')

  const loadData = async () => {
    try {
      const [s, p] = await Promise.all([api.listSessions(), api.listPersonas()])
      setSessions(s)
      setPersonas(p)
    } catch {
      // API not ready yet
    }
  }

  useEffect(() => { loadData() }, [sessionId])

  const handleCreate = () => {
    if (!newName.trim()) return
    onCreateSession(newName.trim(), selectedPersona)
    setShowNew(false)
    setNewName('')
  }

  const handleDelete = async (id: string) => {
    await api.deleteSession(id)
    loadData()
  }

  return (
    <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-gray-800">
        <h1 className="text-sm font-bold text-gray-100 tracking-wide">AgentCSD</h1>
        <p className="text-[10px] text-gray-500 mt-0.5">Conscious Subconscious Dynamic</p>
      </div>

      {/* Connection status */}
      <div className="px-3 py-1.5 border-b border-gray-800 flex items-center gap-1.5">
        <span className={`inline-block w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-[10px] text-gray-400">{connected ? 'Connected' : 'Disconnected'}</span>
      </div>

      {/* Controls */}
      <div className="p-3 border-b border-gray-800 space-y-2">
        <Button variant="primary" size="sm" className="w-full" onClick={() => setShowNew(true)}>
          New Session
        </Button>
        {sessionId && (
          <div className="flex gap-1">
            {running ? (
              <Button variant="secondary" size="sm" className="flex-1" onClick={onPause}>
                Pause
              </Button>
            ) : (
              <Button variant="primary" size="sm" className="flex-1" onClick={onResume}>
                Resume
              </Button>
            )}
          </div>
        )}
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" className="flex-1" onClick={onOpenPersonaEditor}>
            Personas
          </Button>
          <Button variant="ghost" size="sm" className="flex-1" onClick={onOpenConfig}>
            Config
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="px-3 py-2 bg-red-900/30 border-b border-red-800 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Session list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.map(s => (
          <div
            key={s.id}
            className={`group rounded px-2 py-1.5 cursor-pointer transition-colors ${
              s.id === sessionId
                ? 'bg-blue-900/30 border border-blue-800'
                : 'hover:bg-gray-800 border border-transparent'
            }`}
            onClick={() => s.id !== sessionId && onResumeSession(s.id)}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-200 truncate">{s.name}</span>
              <button
                onClick={(e) => { e.stopPropagation(); handleDelete(s.id) }}
                className="text-gray-600 hover:text-red-400 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
              >
                &times;
              </button>
            </div>
            <div className="text-[10px] text-gray-500">
              {s.status} &middot; {new Date(s.updated_at).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>

      {/* New session modal */}
      <Modal open={showNew} onClose={() => setShowNew(false)} title="New Session">
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Session Name</label>
            <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="My session" />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Persona Core</label>
            <select
              value={selectedPersona}
              onChange={e => setSelectedPersona(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-100"
            >
              {personas.map(p => (
                <option key={p.filename} value={p.filename}>{p.filename}</option>
              ))}
            </select>
          </div>
          <Button variant="primary" className="w-full" onClick={handleCreate}>
            Create Session
          </Button>
        </div>
      </Modal>
    </div>
  )
}
