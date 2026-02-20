import { useRef, useEffect, useState } from 'react'
import { useInternalStore, type InternalEntry } from '../stores/internalStore'
import { Card } from './ui/Card'
import { Badge } from './ui/Badge'

function InputContextBlock({ entry }: { entry: InternalEntry }) {
  const [expanded, setExpanded] = useState(false)
  const hasEdUser = !!entry.edUser
  const sLoudCount = entry.sLoudEntries?.length || 0
  const hasMood = !!entry.mood

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
          {sLoudCount > 0 && ` [ ${sLoudCount} S_loud ]`}
          {hasMood && ' [ M&C ]'}
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
          {sLoudCount > 0 && entry.sLoudEntries!.map((s, i) => (
            <div key={i} className="border-l-2 border-blue-700 pl-2">
              <span className="text-blue-400 font-medium">S_loud c{s.cycle ?? '?'}:</span>
              <p className="text-gray-300 whitespace-pre-wrap mt-0.5">{s.content}</p>
            </div>
          ))}
          {hasMood && (
            <div className="border-l-2 border-purple-700 pl-2">
              <span className="text-purple-400 font-medium">Mood:</span>
              <span className="text-gray-300 ml-1">{entry.mood}</span>
              {entry.criteria && (
                <>
                  <br />
                  <span className="text-cyan-400 font-medium">Criteria:</span>
                  <span className="text-gray-300 ml-1">{entry.criteria}</span>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function InternalPanel() {
  const entries = useInternalStore(s => s.entries)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries])

  return (
    <Card
      title="Internal Dialog"
      headerRight={<Badge color="orange">C_model</Badge>}
      className="flex flex-col h-full"
    >
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {entries.length === 0 && (
          <p className="text-gray-600 text-sm text-center py-8">
            Internal dialog will appear here...
          </p>
        )}
        {entries.map((entry, i) => {
          if (entry.type === 'input_context') {
            return <InputContextBlock key={i} entry={entry} />
          }

          const isInternalOnly = entry.internalOnly
          const isLoud = entry.type === 'loud'
          let containerClass: string
          if (isLoud && isInternalOnly) {
            containerClass = 'bg-gray-800/40 border-gray-600/50 text-gray-400'
          } else if (isLoud) {
            containerClass = 'bg-orange-950/30 border-orange-900/50 text-orange-200'
          } else {
            containerClass = 'bg-gray-800/50 border-gray-700/50 text-gray-400 italic'
          }

          let badgeColor: 'orange' | 'gray'
          let badgeLabel: string
          if (isLoud && isInternalOnly) {
            badgeColor = 'gray'
            badgeLabel = 'ID [internal]'
          } else if (isLoud) {
            badgeColor = 'orange'
            badgeLabel = 'ID_loud'
          } else {
            badgeColor = 'gray'
            badgeLabel = 'ID_quiet'
          }

          return (
            <div
              key={i}
              className={`rounded px-3 py-2 text-sm border ${containerClass}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Badge color={badgeColor}>
                  {badgeLabel}
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
