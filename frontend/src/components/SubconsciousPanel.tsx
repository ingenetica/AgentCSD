import { useRef, useEffect } from 'react'
import { useSubconsciousStore } from '../stores/subconsciousStore'
import { Card } from './ui/Card'
import { Badge } from './ui/Badge'

export function SubconsciousPanel() {
  const entries = useSubconsciousStore(s => s.entries)
  const mood = useSubconsciousStore(s => s.mood)
  const criteria = useSubconsciousStore(s => s.criteria)
  const cycle = useSubconsciousStore(s => s.cycle)
  const running = useSubconsciousStore(s => s.running)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries])

  return (
    <Card
      title="Subconscious"
      headerRight={
        <div className="flex items-center gap-2">
          <Badge color="blue">S_model</Badge>
          <Badge color={running ? 'green' : 'red'}>
            {running ? `Cycle ${cycle}` : 'Paused'}
          </Badge>
        </div>
      }
      className="flex flex-col h-full"
    >
      {/* M&C status bar */}
      {(mood || criteria) && (
        <div className="border-b border-gray-800 px-3 py-2 space-y-1">
          {mood && (
            <div className="text-xs">
              <span className="text-gray-500">Mood: </span>
              <span className="text-purple-400">{mood}</span>
            </div>
          )}
          {criteria && (
            <div className="text-xs">
              <span className="text-gray-500">Criteria: </span>
              <span className="text-cyan-400">{criteria}</span>
            </div>
          )}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {entries.length === 0 && (
          <p className="text-gray-600 text-sm text-center py-8">
            Subconscious activity will appear here...
          </p>
        )}
        {entries.map((entry, i) => (
          <div
            key={i}
            className={`rounded px-3 py-2 text-sm border ${
              entry.type === 'loud'
                ? 'bg-blue-950/30 border-blue-900/50 text-blue-200'
                : 'bg-gray-800/50 border-gray-700/50 text-gray-400 italic'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Badge color={entry.type === 'loud' ? 'blue' : 'gray'}>
                {entry.type === 'loud' ? 'S_loud' : 'S_quiet'}
              </Badge>
              {entry.cycle !== undefined && (
                <span className="text-[10px] text-gray-600">cycle {entry.cycle}</span>
              )}
              <span className="text-[10px] text-gray-600 ml-auto">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div className="whitespace-pre-wrap break-words">{entry.content}</div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </Card>
  )
}
