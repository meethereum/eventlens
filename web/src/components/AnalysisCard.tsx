import { motion } from 'framer-motion'
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CardOutput } from '@/types'
import { cardDisplayName, cardDescription, companyNamesInText } from '@/lib/companies'

interface Props {
  card: CardOutput
  onClick: () => void
  disabled?: boolean
}

export default function AnalysisCard({ card, onClick, disabled }: Props) {
  const direction = card.direction ?? 'neutral'
  const title = card.plain_title || cardDisplayName(card.id)
  const summary = companyNamesInText(card.plain_summary || cardDescription(card.id))
  const DirectionIcon = direction === 'against'
    ? ArrowDownRight
    : direction === 'for'
      ? ArrowUpRight
      : Minus

  return (
    <motion.button
      type="button"
      layout
      whileHover={card.status === 'done' && !disabled ? { y: -2 } : {}}
      onClick={card.status === 'done' && !disabled ? onClick : undefined}
      disabled={disabled || card.status !== 'done'}
      className={cn(
        'glass-panel flex min-h-56 w-full flex-col items-start p-5 text-left transition-colors',
        card.status === 'done' && !disabled && 'cursor-pointer hover:border-accent/50',
        card.status === 'error' && 'border-headwind/30',
        disabled && 'opacity-50',
      )}
    >
      <div className="flex w-full items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-base font-semibold leading-6 text-text-primary">{companyNamesInText(title)}</h3>
          {card.status === 'fetching' && <p className="mt-1 text-base text-text-secondary">Gathering data</p>}
          {card.status === 'error' && <p className="mt-1 text-base text-text-secondary">This check is not available</p>}
        </div>
        {card.status === 'done' && (
          <span className={cn(
            'inline-flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-base',
            direction === 'against' && 'border-red-300 text-red-200',
            direction === 'for' && 'border-green-300 text-green-200',
            direction === 'neutral' && 'border-slate-400 text-slate-200',
          )}>
            <DirectionIcon className="h-4 w-4" aria-hidden="true" />
            {direction === 'against' ? 'Against' : direction === 'for' ? 'For' : 'Neutral'}
          </span>
        )}
      </div>

      {card.status === 'done' && (
        <p className="mt-4 max-w-[70ch] text-base leading-7 text-text-secondary">{summary}</p>
      )}
      {card.status === 'queued' && <p className="mt-4 text-base text-text-secondary">Waiting for data</p>}

      <span className="mt-auto inline-flex items-center gap-2 pt-5 text-base font-medium text-text-primary">
        {card.status === 'done' ? 'See details' : card.status === 'error' ? 'Unavailable' : 'Preparing'}
      </span>
    </motion.button>
  )
}
