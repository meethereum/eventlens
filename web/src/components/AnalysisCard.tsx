import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus, AlertCircle, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CardOutput } from '@/types'
import Sparkline from './Sparkline'
import { cardDisplayName, cardDescription } from '@/lib/companies'

interface Props {
  card: CardOutput
  onClick: () => void
  disabled?: boolean
}

function CountUp({ target, decimals = 1 }: { target: number | string; decimals?: number }) {
  const numTarget = typeof target === 'number' ? target : parseFloat(String(target))
  const isNumeric = !isNaN(numTarget)
  const [display, setDisplay] = useState(0)
  const start = useRef(Date.now())
  const duration = 700

  useEffect(() => {
    if (!isNumeric) return
    setDisplay(0)
    start.current = Date.now()
    const frame = () => {
      const elapsed = Date.now() - start.current
      const progress = Math.min(elapsed / duration, 1)
      const ease = 1 - Math.pow(1 - progress, 3)
      setDisplay(numTarget * ease)
      if (progress < 1) requestAnimationFrame(frame)
      else setDisplay(numTarget)
    }
    requestAnimationFrame(frame)
  }, [numTarget, isNumeric])

  if (!isNumeric) return <>{String(target)}</>
  return <>{display.toFixed(decimals)}</>
}

const SIGNAL_CONFIG = {
  tailwind: {
    icon: TrendingUp,
    label: 'Positive signal',
    textColor: 'text-tailwind',
    bgColor: 'bg-tailwind-dim',
    borderColor: 'border-tailwind/20',
    glowClass: 'card-done-tailwind',
    dot: 'bg-tailwind',
  },
  headwind: {
    icon: TrendingDown,
    label: 'Negative signal',
    textColor: 'text-headwind',
    bgColor: 'bg-headwind-dim',
    borderColor: 'border-headwind/20',
    glowClass: 'card-done-headwind',
    dot: 'bg-headwind',
  },
  neutral: {
    icon: Minus,
    label: 'No strong signal',
    textColor: 'text-neutral',
    bgColor: 'bg-neutral-dim',
    borderColor: 'border-neutral/20',
    glowClass: 'card-done-neutral',
    dot: 'bg-neutral',
  },
}

export default function AnalysisCard({ card, onClick, disabled }: Props) {
  const label = card.label as keyof typeof SIGNAL_CONFIG
  const sig = SIGNAL_CONFIG[label] || SIGNAL_CONFIG.neutral
  const SignalIcon = sig.icon

  const isQueued   = card.status === 'queued'
  const isFetching = card.status === 'fetching'
  const isDone     = card.status === 'done'
  const isError    = card.status === 'error'

  const displayName = cardDisplayName(card.id)
  const description = cardDescription(card.id)

  // Format headline value nicely
  const headlineVal = card.headline
    ? (typeof card.headline.value === 'number'
        ? card.headline.value
        : card.headline.value)
    : null

  const sparkColor = label === 'tailwind' ? '#10b981' : label === 'headwind' ? '#ef4444' : '#6b7280'

  return (
    <motion.div
      layout
      whileHover={isDone && !disabled ? { y: -2 } : {}}
      onClick={isDone && !disabled ? onClick : undefined}
      className={cn(
        'glass-panel p-5 relative overflow-hidden transition-all duration-300 group',
        isDone && !disabled && 'cursor-pointer',
        isDone && sig.glowClass,
        isFetching && 'card-fetching',
        isError && 'border-headwind/30',
        disabled && 'opacity-50',
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-text-primary truncate">{displayName}</h3>
          <p className="text-xs text-text-muted truncate">{description}</p>
        </div>

        {/* Signal badge — only on done */}
        {isDone && (
          <div className={cn(
            'flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border shrink-0',
            sig.bgColor, sig.textColor, sig.borderColor,
          )}>
            <SignalIcon className="w-3 h-3" />
            <span className="hidden sm:inline">{sig.label}</span>
          </div>
        )}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {(isQueued || isFetching) && (
          <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className={cn('skeleton h-8 w-28 rounded-lg mb-3', isFetching && 'animate-pulse')} />
            <div className="skeleton h-3 w-full rounded mb-2" />
            <div className="skeleton h-3 w-3/4 rounded mb-4" />
            <div className="skeleton h-14 w-full rounded" />
            {isFetching && (
              <div className="flex items-center gap-1.5 mt-2 text-xs text-accent-glow">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                Fetching data…
              </div>
            )}
          </motion.div>
        )}

        {isDone && headlineVal !== null && (
          <motion.div
            key="done"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="space-y-4"
          >
            {/* Big headline number */}
            <div>
              <div className="text-3xl font-mono font-bold tabular-nums"
                   style={{ color: label === 'tailwind' ? '#10b981' : label === 'headwind' ? '#ef4444' : '#94a3b8' }}>
                <CountUp
                  target={typeof headlineVal === 'number' ? headlineVal : headlineVal}
                  decimals={typeof headlineVal === 'number' && Math.abs(headlineVal) > 100 ? 0 : 2}
                />
                {card.headline?.unit && (
                  <span className="text-lg text-text-muted ml-1 font-sans font-normal">
                    {card.headline.unit}
                  </span>
                )}
              </div>
              <div className="text-xs text-text-muted mt-0.5">{card.headline?.label}</div>
            </div>

            {/* Sparkline */}
            {card.series.length > 0 && (
              <div className="h-14">
                <Sparkline data={card.series} color={sparkColor} height={56} />
              </div>
            )}

            {/* Top 2 metrics in plain English */}
            <div className="grid grid-cols-2 gap-2">
              {card.metrics.slice(0, 2).map((m, i) => (
                <div key={i} className="bg-surface-3/60 rounded-lg px-3 py-2">
                  <div className="text-2xs text-text-muted mb-0.5">{m.name}</div>
                  <div className="text-sm font-mono font-medium text-text-primary tabular-nums">
                    {m.value !== null && m.value !== undefined
                      ? `${m.value}${m.unit ? ' ' + m.unit : ''}`
                      : '—'}
                  </div>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-1 border-t border-border/50">
              <div className="flex items-center gap-1.5">
                {/* Quality bar */}
                <div className="flex items-center gap-1 text-2xs text-text-muted">
                  <div className="w-16 h-1 bg-surface-3 rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full', card.quality >= 0.8 ? 'bg-tailwind' : card.quality >= 0.5 ? 'bg-amber' : 'bg-headwind')}
                      style={{ width: `${card.quality * 100}%` }}
                    />
                  </div>
                  <span>Data quality</span>
                </div>
              </div>
              <div className="flex items-center gap-1 text-2xs text-text-muted group-hover:text-accent-glow transition-colors">
                <span>Details</span>
                <ChevronRight className="w-3 h-3" />
              </div>
            </div>

            {/* Warning */}
            {card.warnings.length > 0 && (
              <div className="flex items-start gap-1.5 text-xs text-amber bg-amber-muted/50 rounded-lg px-3 py-2">
                <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <span>{card.warnings[0]}</span>
              </div>
            )}
          </motion.div>
        )}

        {isError && (
          <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="py-2">
            <div className="flex items-center gap-2 text-sm text-headwind mb-2">
              <AlertCircle className="w-4 h-4" />
              <span>Couldn't load this data</span>
            </div>
            <p className="text-xs text-text-muted">{card.error_message ?? 'Data source unavailable'}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
