import { useState } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { Sidebar } from './Sidebar'
import { ChatPanel } from './ChatPanel'
import { InternalPanel } from './InternalPanel'
import { SubconsciousPanel } from './SubconsciousPanel'
import { PersonaEditor } from './PersonaEditor'
import { ConfigPanel } from './ConfigPanel'

export function Layout() {
  const { send } = useWebSocket()
  const [showPersona, setShowPersona] = useState(false)
  const [showConfig, setShowConfig] = useState(false)

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

      <div className="flex-1 flex min-w-0">
        {/* Observation panels - LEFT (wider) */}
        <div className="flex-[2] border-r border-gray-800 flex flex-col min-w-0">
          <div className="flex-1 min-h-0 border-b border-gray-800">
            <InternalPanel />
          </div>
          <div className="flex-1 min-h-0">
            <SubconsciousPanel />
          </div>
        </div>

        {/* External Dialog - RIGHT (narrower) */}
        <div className="flex-1 min-w-0 flex flex-col">
          <ChatPanel onSend={(content) => send({ type: 'user_message', content })} />
        </div>
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
