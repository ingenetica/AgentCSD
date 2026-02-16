import { ReactNode } from 'react'

interface CardProps {
  title?: string
  headerRight?: ReactNode
  className?: string
  children: ReactNode
}

export function Card({ title, headerRight, className = '', children }: CardProps) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-lg overflow-hidden ${className}`}>
      {title && (
        <div className="flex items-center justify-between px-3 py-2 border-b border-gray-800">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{title}</h3>
          {headerRight}
        </div>
      )}
      {children}
    </div>
  )
}
