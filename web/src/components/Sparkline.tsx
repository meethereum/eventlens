import { useMemo } from 'react'
import type { Series } from '@/types'

interface Props {
  data: Series[]
  color: string
  height?: number
  width?: number
}

export default function Sparkline({ data, color, height = 48, width = 200 }: Props) {
  const points = useMemo(() => {
    const valid = data.filter(d => d.v !== null) as Array<{ t: string; v: number }>
    if (valid.length < 2) return null

    const vals = valid.map(d => d.v)
    const min = Math.min(...vals)
    const max = Math.max(...vals)
    const range = max - min || 1
    const pad = 2

    const coords = valid.map((d, i) => {
      const x = (i / (valid.length - 1)) * (width - pad * 2) + pad
      const y = height - pad - ((d.v - min) / range) * (height - pad * 2)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })

    // Area fill path
    const first = coords[0].split(',')
    const last = coords[coords.length - 1].split(',')
    const area = `M${first[0]},${height} L${coords.join(' L')} L${last[0]},${height} Z`

    return { line: coords.join(' '), area }
  }, [data, height, width])

  if (!points) return null

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="w-full"
      style={{ height }}
    >
      <defs>
        <linearGradient id={`sg-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {/* Area fill */}
      <path
        d={points.area}
        fill={`url(#sg-${color.replace('#', '')})`}
      />
      {/* Line */}
      <polyline
        points={points.line}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
