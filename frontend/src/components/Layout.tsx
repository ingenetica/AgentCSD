import { useState, useRef, useCallback, useEffect } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { Sidebar } from './Sidebar'
import { ChatPanel } from './ChatPanel'
import { InternalPanel } from './InternalPanel'
import { SubconsciousPanel } from './SubconsciousPanel'
import { PersonaEditor } from './PersonaEditor'
import { ConfigPanel } from './ConfigPanel'

function useResize(
  direction: 'horizontal' | 'vertical',
  initial: number,
  min: number,
  max: number,
) {
  const [size, setSize] = useState(initial)
  const dragging = useRef(false)
  const startPos = useRef(0)
  const startSize = useRef(0)

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      dragging.current = true
      startPos.current = direction === 'horizontal' ? e.clientX : e.clientY
      startSize.current = size
      document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize'
      document.body.style.userSelect = 'none'
    },
    [direction, size],
  )

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return
      const pos = direction === 'horizontal' ? e.clientX : e.clientY
      const delta = pos - startPos.current
      const next = Math.min(max, Math.max(min, startSize.current + delta))
      setSize(next)
    }
    const onMouseUp = () => {
      if (!dragging.current) return
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [direction, min, max])

  return { size, onMouseDown }
}

export function Layout() {
  const { send } = useWebSocket()
  const [showPersona, setShowPersona] = useState(false)
  const [showConfig, setShowConfig] = useState(false)

  // Horizontal split: left column width in px (chat + internal)
  const hResize = useResize('horizontal', Math.round(window.innerWidth * 0.55), 300, window.innerWidth - 400)
  // Vertical split: chat panel height in % of left column
  const [chatPct, setChatPct] = useState(50)
  const leftColRef = useRef<HTMLDivElement>(null)
  const vDragging = useRef(false)
  const vStartY = useRef(0)
  const vStartPct = useRef(50)

  const onVMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    vDragging.current = true
    vStartY.current = e.clientY
    vStartPct.current = chatPct
    document.body.style.cursor = 'row-resize'
    document.body.style.userSelect = 'none'
  }, [chatPct])

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!vDragging.current || !leftColRef.current) return
      const colHeight = leftColRef.current.getBoundingClientRect().height
      if (colHeight === 0) return
      const delta = e.clientY - vStartY.current
      const deltaPct = (delta / colHeight) * 100
      const next = Math.min(85, Math.max(15, vStartPct.current + deltaPct))
      setChatPct(next)
    }
    const onMouseUp = () => {
      if (!vDragging.current) return
      vDragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [])

  return (
    <div className="h-screen flex">
      <Sidebar
        onCreateSession={(name, persona) =>
          send({ type: 'create_session', name, persona_core: persona })
        }
        onResumeSession={(id) => send({ type: 'resume_session', session_id: id })}
        onPause={() => send({ type: 'pause_session' })}
        onResume={() => send({ type: 'resume_loop' })}
        onOpenPersonaEditor={() => setShowPersona(true)}
        onOpenConfig={() => setShowConfig(true)}
      />

      {/* Left column: External Dialog (top) + Internal Dialog (bottom) */}
      <div
        ref={leftColRef}
        className="flex flex-col min-w-0 border-r border-gray-800"
        style={{ width: hResize.size, flexShrink: 0 }}
      >
        <div className="min-h-0 overflow-hidden" style={{ height: `${chatPct}%` }}>
          <ChatPanel onSend={(content) => send({ type: 'user_message', content })} />
        </div>
        {/* Vertical resize handle */}
        <div
          className="h-1.5 bg-gray-800 hover:bg-blue-600 cursor-row-resize flex-shrink-0 transition-colors"
          onMouseDown={onVMouseDown}
        />
        <div className="flex-1 min-h-0 overflow-hidden">
          <InternalPanel />
        </div>
      </div>

      {/* Horizontal resize handle */}
      <div
        className="w-1.5 bg-gray-800 hover:bg-blue-600 cursor-col-resize flex-shrink-0 transition-colors"
        onMouseDown={hResize.onMouseDown}
      />

      {/* Right column: Subconscious */}
      <div className="flex-1 min-w-0 flex flex-col">
        <SubconsciousPanel />
      </div>

      <PersonaEditor open={showPersona} onClose={() => setShowPersona(false)} />
      <ConfigPanel
        open={showConfig}
        onClose={() => setShowConfig(false)}
        onUpdateConfig={(config) => send({ type: 'update_config', model_config: config })}
      />
    </div>
  )
}
