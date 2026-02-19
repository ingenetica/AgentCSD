import { useRef, useEffect } from 'react'
import { useInternalStore } from '../stores/internalStore'
import { Card } from './ui/Card'
import { Badge } from './ui/Badge'

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
