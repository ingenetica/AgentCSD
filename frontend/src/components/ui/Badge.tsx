interface BadgeProps {
  color?: 'green' | 'orange' | 'blue' | 'red' | 'gray'
  children: React.ReactNode
}

const colors = {
  green: 'bg-green-900/50 text-green-400 border-green-700',
  orange: 'bg-orange-900/50 text-orange-400 border-orange-700',
  blue: 'bg-blue-900/50 text-blue-400 border-blue-700',
  red: 'bg-red-900/50 text-red-400 border-red-700',
  gray: 'bg-gray-800 text-gray-400 border-gray-600',
}

export function Badge({ color = 'gray', children }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border ${colors[color]}`}>
      {children}
    </span>
  )
}
