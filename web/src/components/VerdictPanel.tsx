import { motion } from 'framer-motion'
import { ArrowDownRight, ArrowUpRight, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AggregateResult, CardOutput, VerdictOutput } from '@/types'

interface Props {
  verdict: VerdictOutput | null
  verdictStream: string
  cards: Record<string, CardOutput>
  aggregate: AggregateResult | null
  onFindingClick: (findingId: string) => void
}

const DIRECTIONS = [
  { id: 'against', label: 'Working against', color: 'bg-red-400', text: 'text-red-300' },
  { id: 'mixed', label: 'Mixed', color: 'bg-amber-300', text: 'text-amber-200' },
  { id: 'for', label: 'In its favor', color: 'bg-green-400', text: 'text-green-300' },
] as const

const STRENGTH_LEVELS = { strong: 3, moderate: 2, slight: 1 } as const

function strengthDots(strength: 'strong' | 'moderate' | 'slight') {
  const active = STRENGTH_LEVELS[strength]
  return (
    <span className="flex items-center gap-1" aria-label={`Strength: ${strength}`} title={`Strength: ${strength}`}>
      {[1, 2, 3].map(dot => (
        <span
          key={dot}
          className={cn(
            'h-2.5 w-2.5 rounded-full border border-slate-400',
            dot <= active ? 'bg-slate-200' : 'bg-transparent',
          )}
        />
      ))}
    </span>
  )
}

function splitPercentages(split: Record<'against' | 'mixed' | 'for', number> | undefined) {
  const total = split ? split.against + split.mixed + split.for : 0
  if (!split || total <= 0) return { against: 0, mixed: 100, for: 0 }
  const against = Math.round(split.against / total * 100)
  const mixed = Math.round(split.mixed / total * 100)
  return { against, mixed, for: 100 - against - mixed }
}

function FindingColumn({
  direction,
  title,
  points,
  onFindingClick,
}: {
  direction: 'against' | 'for'
  title: string
  points: NonNullable<VerdictOutput['points']>
  onFindingClick: (findingId: string) => void
}) {
  const matches = points.filter(point => point.direction === direction)
  const Icon = direction === 'against' ? ArrowDownRight : ArrowUpRight
  const barColor = direction === 'against' ? 'bg-red-400' : 'bg-green-400'
  const iconColor = direction === 'against' ? 'text-red-300' : 'text-green-300'

  return (
    <section className="min-w-0 rounded-2xl border border-border bg-surface-1 p-5 sm:p-6">
      <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-text-primary">
        <Icon className={cn('h-5 w-5 shrink-0', iconColor)} aria-hidden="true" />
        {title}
      </h3>
      {matches.length === 0 ? (
        <p className="text-base leading-7 text-text-secondary">Nothing meaningful found here.</p>
      ) : (
        <div className="space-y-4">
          {matches.map((point, index) => (
            <article
              key={`${point.title}-${index}`}
              className="grid grid-cols-[4px_minmax(0,1fr)_auto] items-start gap-3"
            >
              <span className={cn('mt-1 h-full min-h-16 rounded-full', barColor)} aria-hidden="true" />
              <div className="min-w-0 space-y-2">
                <h4 className="text-base font-semibold leading-6 text-text-primary">{point.title}</h4>
                <p className="max-w-[70ch] text-base leading-7 text-text-secondary">{point.explanation}</p>
                <button
                  type="button"
                  onClick={() => point.findings[0] && onFindingClick(point.findings[0])}
                  disabled={point.findings.length === 0}
                  className="inline-flex min-h-10 items-center gap-1 rounded-full border border-slate-400 px-3 text-base text-text-primary transition-colors hover:border-accent-glow hover:text-accent-glow disabled:opacity-50"
                >
                  See details
                  <ChevronRight className="h-4 w-4" aria-hidden="true" />
                </button>
              </div>
              <div className="pt-1">{strengthDots(point.strength)}</div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

export default function VerdictPanel({ verdict, verdictStream, cards, aggregate, onFindingClick }: Props) {
  const points = verdict?.points ?? []
  const percentages = splitPercentages(verdict?.scenario_split)
  const scenarioDescriptions = verdict?.scenarios ?? []
  const isDebug = new URLSearchParams(window.location.search).get('debug') === '1'
  const doneCount = Object.values(cards).filter(card => card.status === 'done').length

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mx-auto w-full max-w-5xl space-y-7 text-base"
    >
      <section className="rounded-2xl border border-border bg-surface-1 p-6 sm:p-8">
        {verdict ? (
          <>
            <h2 className="max-w-[70ch] text-2xl font-semibold leading-tight text-text-primary sm:text-3xl">
              {verdict.headline}
            </h2>
            <p className="mt-5 max-w-[70ch] text-lg leading-8 text-text-secondary sm:text-xl">
              {verdict.answer}
            </p>
          </>
        ) : verdictStream ? (
          <div aria-live="polite">
            <h2 className="text-2xl font-semibold text-text-primary">Preparing the evidence summary</h2>
            <p className="mt-5 max-w-[70ch] text-lg leading-8 text-text-secondary">{verdictStream}</p>
          </div>
        ) : (
          <div className="space-y-4" aria-label="Preparing the evidence summary">
            <div className="skeleton h-8 w-3/4 rounded-lg" />
            <div className="skeleton h-5 w-full rounded" />
            <div className="skeleton h-5 w-5/6 rounded" />
          </div>
        )}
      </section>

      <div className="flex flex-wrap gap-3">
        <div className="rounded-full border border-border bg-surface-1 px-4 py-2 text-base text-text-primary">
          Evidence leans: <strong>{verdict ? (verdict.scenario_split?.for ?? 0) > (verdict.scenario_split?.against ?? 0) + 0.03 ? 'Positive' : (verdict.scenario_split?.against ?? 0) > (verdict.scenario_split?.for ?? 0) + 0.03 ? 'Negative' : 'Mixed' : 'Mixed'}</strong>
        </div>
        <div className="rounded-full border border-border bg-surface-1 px-4 py-2 text-base text-text-primary">
          How sure: <strong>{verdict?.how_sure_level ?? 'Low'}</strong>
        </div>
      </div>
      {verdict?.how_sure_reason && (
        <p className="max-w-[70ch] text-base leading-7 text-text-secondary">{verdict.how_sure_reason}</p>
      )}

      <section className="rounded-2xl border border-border bg-surface-1 p-5 sm:p-6" aria-label="How the evidence splits">
        <h3 className="mb-4 text-lg font-semibold text-text-primary">How the evidence splits</h3>
        <div className="flex h-8 w-full overflow-hidden rounded-full bg-surface-3" role="img" aria-label={`Working against ${percentages.against} percent, mixed ${percentages.mixed} percent, in its favor ${percentages.for} percent`}>
          {DIRECTIONS.map(item => {
            const value = percentages[item.id]
            return value > 0 ? (
              <span key={item.id} className={item.color} style={{ width: `${value}%` }} />
            ) : null
          })}
        </div>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-base text-text-primary">
          {DIRECTIONS.map(item => (
            <span key={item.id} className="inline-flex items-center gap-2">
              <span className={cn('h-3 w-3 rounded-sm', item.color)} aria-hidden="true" />
              {item.label} {percentages[item.id]}%
            </span>
          ))}
        </div>
        <p className="mt-3 text-base leading-7 text-text-secondary">
          This shows how the evidence splits. It is not the chance the price will move.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <FindingColumn
          direction="against"
          title="What's pulling it down"
          points={points}
          onFindingClick={onFindingClick}
        />
        <FindingColumn
          direction="for"
          title="What's holding it up"
          points={points}
          onFindingClick={onFindingClick}
        />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <section className="rounded-2xl border border-border bg-surface-1 p-5 sm:p-6">
          <h3 className="mb-3 text-lg font-semibold text-text-primary">What we can't tell from this data</h3>
          {(verdict?.unknowns ?? []).length ? (
            <ul className="space-y-2 text-base leading-7 text-text-secondary">
              {verdict?.unknowns?.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
            </ul>
          ) : (
            <p className="text-base leading-7 text-text-secondary">The available findings do not answer every question about this event.</p>
          )}
        </section>

        <section className="rounded-2xl border border-border bg-surface-1 p-5 sm:p-6">
          <h3 className="mb-3 text-lg font-semibold text-text-primary">What to keep an eye on</h3>
          {(verdict?.watch ?? []).length ? (
            <ul className="space-y-4">
              {verdict?.watch?.map((item, index) => (
                <li key={`${item.what}-${index}`} className="space-y-1">
                  <p className="text-base font-semibold leading-6 text-text-primary">{item.what}</p>
                  <p className="text-base leading-7 text-text-secondary">{item.why}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-base leading-7 text-text-secondary">No specific follow up checks are available yet.</p>
          )}
        </section>
      </div>

      <details className="rounded-2xl border border-border bg-surface-1 p-5 sm:p-6">
        <summary className="cursor-pointer text-lg font-semibold text-text-primary">How we scored this</summary>
        <p className="mt-3 max-w-[70ch] text-base leading-7 text-text-secondary">
          The three descriptions below show how the current findings could be grouped. They are summaries of the evidence, not forecasts.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          {scenarioDescriptions.map(scenario => (
            <article key={scenario.id} className="rounded-xl border border-border bg-surface-2 p-4">
              <h4 className="text-base font-semibold text-text-primary">{scenario.name}</h4>
              <p className="mt-2 text-base leading-7 text-text-secondary">{scenario.what_it_looks_like}</p>
              <p className="mt-2 text-base leading-7 text-text-secondary">{scenario.signs}</p>
            </article>
          ))}
        </div>
        {isDebug && (
          <div className="mt-5 border-t border-border pt-4 text-base leading-7 text-text-secondary">
            <p>Agreement: {aggregate?.evidence_strength.toFixed(3) ?? 'not available'}</p>
            <p>Coverage: {aggregate?.coverage.toFixed(3) ?? 'not available'} across {doneCount} of 10 checks</p>
            <p>Combined score: {aggregate?.composite_signal.toFixed(3) ?? 'not available'}</p>
          </div>
        )}
      </details>
    </motion.section>
  )
}
