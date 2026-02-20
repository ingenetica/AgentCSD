import { useRef, useEffect, useState } from 'react'
import { useSubconsciousStore, type SubconsciousEntry } from '../stores/subconsciousStore'
import { Card } from './ui/Card'
import { Badge } from './ui/Badge'

function truncate(s: string, max: number) {
  return s.length > max ? s.slice(0, max) + '...' : s
}

function SInputContextBlock({ entry }: { entry: SubconsciousEntry }) {
  const [expanded, setExpanded] = useState(false)
  const hasEdUser = !!entry.edUser
  const hasEdAgent = !!entry.edAgent
  const hasIdLoud = !!entry.idLoud
  const hasIdQuiet = !!entry.idQuiet
  const hasAny = hasEdUser || hasEdAgent || hasIdLoud || hasIdQuiet

  return (
    <div
      className="rounded px-3 py-2 text-xs border border-dashed border-gray-700/60 bg-gray-900/40 cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center gap-2 mb-1">
        <Badge color="gray">INPUT</Badge>
        {entry.cycle !== undefined && (
          <span className="text-[10px] text-gray-600">cycle {entry.cycle}</span>
        )}
        <span className="text-gray-500 ml-1">
          {hasEdUser && '[ ED_user ]'}
          {hasEdAgent && ' [ ED_agent ]'}
          {hasIdLoud && ' [ ID_loud ]'}
          {hasIdQuiet && ' [ ID_quiet ]'}
          {!hasAny && '[ no new input ]'}
        </span>
        <span className="text-[10px] text-gray-600 ml-auto">
          {expanded ? '▼' : '▶'}
        </span>
      </div>
      {expanded && (
        <div className="mt-2 space-y-2">
          {hasEdUser && (
            <div className="border-l-2 border-green-700 pl-2">
              <span className="text-green-500 font-medium">ED_user:</span>
              <p className="text-gray-300 whitespace-pre-wrap mt-0.5">{entry.edUser}</p>
            </div>
          )}
          {hasEdAgent && (
            <div className="border-l-2 border-orange-700 pl-2">
              <span className="text-orange-400 font-medium">ED_agent:</span>
              <p className="text-gray-300 whitespace-pre-wrap mt-0.5">{truncate(entry.edAgent!, 500)}</p>
            </div>
          )}
          {hasIdLoud && (
            <div className="border-l-2 border-yellow-700 pl-2">
              <span className="text-yellow-400 font-medium">ID_loud:</span>
              <p className="text-gray-300 whitespace-pre-wrap mt-0.5">{truncate(entry.idLoud!, 500)}</p>
            </div>
          )}
          {hasIdQuiet && (
            <div className="border-l-2 border-gray-600 pl-2">
              <span className="text-gray-400 font-medium">ID_quiet:</span>
              <p className="text-gray-400 whitespace-pre-wrap mt-0.5">{truncate(entry.idQuiet!, 300)}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

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
        {entries.map((entry, i) => {
          if (entry.type === 'input_context') {
            return <SInputContextBlock key={i} entry={entry} />
          }

          return (
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
          )
        })}
        <div ref={bottomRef} />
      </div>
    </Card>
  )
}
