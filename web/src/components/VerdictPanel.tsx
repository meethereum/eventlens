import { motion } from 'framer-motion'
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { VerdictOutput, AggregateResult, CardOutput } from '@/types'
import { cardDisplayName } from '@/lib/companies'

interface Props {
  verdict: VerdictOutput | null
  aggregate: AggregateResult | null
  verdictStream: string
  cards: Record<string, CardOutput>
  onCitationClick: (cardId: string) => void
  ticker?: string
}

// Replaces [C3] with a human-readable chip showing the card's plain name
function CitedText({
  text,
  onCitationClick,
  validCards,
}: {
  text: string
  onCitationClick: (id: string) => void
  validCards?: Set<string>
}) {
  const parts = text.split(/(\[C\d+\])/g)
  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^\[([C]\d+)\]$/)
        if (match) {
          const cardId = match[1]
          const isInvalid = validCards !== undefined && !validCards.has(cardId)
          const name = cardDisplayName(cardId)
          return (
            <button
              key={i}
              onClick={() => onCitationClick(cardId)}
              title={isInvalid ? `${cardId}: not found` : `Open: ${name}`}
              className={cn(
                'inline-flex items-center gap-1 mx-0.5 px-2 py-0.5 rounded-md text-xs font-medium',
                'border transition-colors cursor-pointer',
                isInvalid
                  ? 'bg-amber-muted text-amber border-amber/20'
                  : 'bg-accent-muted text-accent-glow border-accent/20 hover:bg-accent/20',
              )}
            >
              <span>{name}</span>
              {isInvalid && <span className="text-amber">⚠</span>}
            </button>
          )
        }
        return <span key={i}>{part}</span>
      })}
    </>
  )
}
export default function VerdictPanel({
  verdict, aggregate, verdictStream, cards, onCitationClick, ticker,
}: Props) {
  const isStreaming = !verdict && verdictStream.length > 0
  const compName = ticker
    ? (({ NVDA:'Nvidia', INTC:'Intel', AAPL:'Apple', MSFT:'Microsoft', GM:'General Motors',
           SBUX:'Starbucks', AMZN:'Amazon', DIS:'Disney', BA:'Boeing', RTX:'RTX',
           XOM:'ExxonMobil', CVX:'Chevron', JPM:'JPMorgan Chase', SCHW:'Charles Schwab', UNH:'UnitedHealth',
         } as Record<string,string>)[ticker.toUpperCase()] ?? ticker)
    : 'this company'
  const validCards = new Set(Object.keys(cards).filter(id => id !== '_refusal'))

  // Determine overall direction from aggregate
  const composite = aggregate?.composite_signal ?? 0
  const direction = composite > 0.1 ? 'positive' : composite < -0.1 ? 'negative' : 'mixed'
  const directionColors = {
    positive: { text: 'text-tailwind', bg: 'bg-tailwind/10', border: 'border-tailwind/20', icon: TrendingUp },
    negative: { text: 'text-headwind', bg: 'bg-headwind/10', border: 'border-headwind/20', icon: TrendingDown },
    mixed:    { text: 'text-neutral',  bg: 'bg-neutral/10',  border: 'border-neutral/20',  icon: Minus },
  }
  const dc = directionColors[direction]
  const DirIcon = dc.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-5"
    >
      {/* Section header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary">What this means</h2>
        <div className="flex items-center gap-2">
          {verdict?.is_fallback && (
            <span className="text-2xs text-amber border border-amber/20 bg-amber-muted px-2 py-1 rounded-full">
              Auto-generated summary
            </span>
          )}
          {verdict && !verdict.is_fallback && (
            <span className="text-2xs text-tailwind border border-tailwind/20 bg-tailwind-dim px-2 py-1 rounded-full">
              AI-verified
            </span>
          )}
          {verdict?.is_fallback_model && (
            <span className="text-2xs text-amber border border-amber/20 bg-amber-muted px-2 py-1 rounded-full">
              Using backup model
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* ── Left: main narrative ── */}
        <div className="xl:col-span-2 space-y-5">

          {/* Overall direction banner */}
          {aggregate && (
            <div className={cn(
              'flex items-center gap-4 p-4 rounded-xl border',
              dc.bg, dc.border,
            )}>
              <div className={cn('w-10 h-10 rounded-full flex items-center justify-center shrink-0', dc.bg, 'border', dc.border)}>
                <DirIcon className={cn('w-5 h-5', dc.text)} />
              </div>
              <div className="flex-1 min-w-0">
                <div className={cn('text-sm font-semibold', dc.text)}>
                  {direction === 'positive' && `Overall picture looks positive for ${compName}`}
                  {direction === 'negative' && `Overall picture looks challenging for ${compName}`}
                  {direction === 'mixed'    && `Mixed picture — some good, some bad for ${compName}`}
                </div>
                <div className="text-xs text-text-muted mt-0.5">
                  Based on {Object.values(cards).filter(c => c.status === 'done').length} data sources analysed
                </div>
              </div>
              {verdict && (
                <div className={cn('text-2xl font-mono font-bold tabular-nums shrink-0', dc.text)}>
                  {composite > 0 ? '+' : ''}{composite.toFixed(2)}
                </div>
              )}
            </div>
          )}

          {/* Headline + summary */}
          <div className="glass-panel p-6">
            {isStreaming ? (
              <>
                <div className="skeleton h-6 w-3/4 rounded-lg mb-4" />
                <p className="text-base text-text-secondary leading-relaxed">
                  {verdictStream}
                  <span className="inline-block w-0.5 h-5 bg-accent-glow ml-0.5 animate-pulse align-middle" />
                </p>
              </>
            ) : verdict ? (
              <>
                <h3 className="text-lg font-semibold text-text-primary leading-snug mb-4">
                  {verdict.headline}
                </h3>
                <p className="text-base text-text-secondary leading-relaxed">
                  <CitedText
                    text={verdict.summary}
                    onCitationClick={onCitationClick}
                    validCards={validCards}
                  />
                </p>
              </>
            ) : (
              <div className="space-y-3">
                <div className="skeleton h-6 w-3/4 rounded-lg" />
                <div className="skeleton h-4 w-full rounded" />
                <div className="skeleton h-4 w-5/6 rounded" />
                <div className="skeleton h-4 w-4/6 rounded" />
              </div>
            )}
          </div>

          {/* Key factors */}
          {verdict && verdict.key_drivers.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* What's working for it */}
              <div className="glass-panel p-4 border-tailwind/10">
                <h4 className="text-sm font-semibold text-tailwind mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Working in its favor
                </h4>
                <ul className="space-y-3">
                  {verdict.counter_evidence.length > 0 && verdict.key_drivers
                    .filter(kd => {
                      const card = cards[kd.card]
                      const lbl = card?.label ?? null
                      return lbl === 'tailwind'
                    })
                    .concat(verdict.key_drivers.slice(0, 2))
                    .slice(0, 3)
                    .map((kd, i) => (
                      <li key={i} className="flex gap-2.5 text-sm text-text-secondary">
                        <button
                          onClick={() => onCitationClick(kd.card)}
                          className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-surface-3 text-text-muted hover:text-accent-glow transition-colors shrink-0 mt-0.5"
                        >
                          {cardDisplayName(kd.card)}
                        </button>
                        <span className="leading-relaxed">{kd.point}</span>
                      </li>
                    ))}
                  {verdict.key_drivers.length === 0 && (
                    <li className="text-sm text-text-muted italic">No strong positive factors identified.</li>
                  )}
                </ul>
              </div>

              {/* What's working against it */}
              <div className="glass-panel p-4 border-headwind/10">
                <h4 className="text-sm font-semibold text-headwind mb-3 flex items-center gap-2">
                  <TrendingDown className="w-4 h-4" />
                  Working against it
                </h4>
                <ul className="space-y-3">
                  {verdict.counter_evidence.map((ce, i) => (
                    <li key={i} className="flex gap-2.5 text-sm text-text-secondary">
                      <button
                        onClick={() => onCitationClick(ce.card)}
                        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-surface-3 text-text-muted hover:text-headwind transition-colors shrink-0 mt-0.5"
                      >
                        {cardDisplayName(ce.card)}
                      </button>
                      <span className="leading-relaxed">{ce.point}</span>
                    </li>
                  ))}
                  {verdict.counter_evidence.length === 0 && (
                    <li className="text-sm text-text-muted italic">No strong negative factors identified.</li>
                  )}
                </ul>
              </div>
            </div>
          )}

          {/* Three scenarios */}
          {verdict?.scenarios && verdict.scenarios.length > 0 && (
            <div className="glass-panel p-5">
              <h4 className="text-sm font-semibold text-text-secondary mb-1">Three possible outcomes</h4>
              <p className="text-xs text-text-muted mb-4">
                Based on how the evidence stacks up — not a prediction of what will happen.
              </p>
              <div className="space-y-4">
                {[...verdict.scenarios]
                  .sort((a, b) => b.score - a.score)
                  .map((sc, i) => {
                    const isLikely = i === 0
                    const color = sc.name.includes('Tailwind') ? '#10b981'
                                : sc.name.includes('Headwind') ? '#ef4444'
                                : '#f59e0b'
                    return (
                      <div key={sc.name}>
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-text-primary">
                              {sc.name.replace('-dominant', '')}
                            </span>
                            {isLikely && (
                              <span className="text-2xs font-medium px-1.5 py-0.5 rounded-full border"
                                    style={{ color, borderColor: color + '40', background: color + '15' }}>
                                Most supported
                              </span>
                            )}
                          </div>
                        </div>
                        {sc.rationale && (
                          <p className="text-xs text-text-muted leading-relaxed">{sc.rationale}</p>
                        )}
                        {sc.watch_for && (
                          <p className="text-xs text-text-muted mt-1">
                            <span className="text-text-secondary font-medium">Watch for: </span>
                            {sc.watch_for}
                          </p>
                        )}
                      </div>
                    )
                  })}
              </div>
            </div>
          )}

          {/* Data gaps */}
          {verdict?.data_gaps && verdict.data_gaps.length > 0 && (
            <div className="glass-panel p-4 border-amber/10">
              <h4 className="text-xs font-semibold text-amber mb-2 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> What we couldn't fully measure
              </h4>
              <ul className="space-y-1">
                {verdict.data_gaps.map((g, i) => (
                  <li key={i} className="text-xs text-amber/80 leading-relaxed">{g}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Disclaimer */}
          {verdict?.disclaimer && (
            <p className="text-xs text-text-muted border border-border/50 rounded-lg px-4 py-3 leading-relaxed bg-surface-2/50">
              <strong className="text-text-secondary">Important: </strong>{verdict.disclaimer}
            </p>
          )}
        </div>

        {/* ── Right: confidence summary ── */}
        <div className="space-y-4">
          {aggregate && (
            <>
              <div className="glass-panel p-5">
                <h4 className="text-sm font-semibold text-text-primary">How confident are we?</h4>
                <p className="mt-2 text-lg font-medium text-text-secondary">
                  {aggregate.evidence_strength >= 0.55
                    ? 'Higher confidence'
                    : aggregate.evidence_strength >= 0.3
                      ? 'Moderate confidence'
                      : 'Limited confidence'}
                </p>
                <p className="mt-1 text-xs text-text-muted">
                  {aggregate.coverage >= 0.8
                    ? 'Most evidence sources were available.'
                    : aggregate.coverage >= 0.5
                      ? 'Some evidence sources were unavailable.'
                      : 'Many evidence sources were unavailable.'}
                </p>
              </div>
              <details className="glass-panel p-4 text-xs text-text-muted">
                <summary className="cursor-pointer">How was this calculated?</summary>
                <p className="mt-2">
                  Confidence reflects agreement among the available evidence sources; coverage reflects
                  how many sources returned usable data. The overall direction combines each source's
                  signal, reliability, and contribution.
                </p>
                <p className="mt-2">
                  Debug values — agreement: {aggregate.evidence_strength.toFixed(3)}, coverage: {aggregate.coverage.toFixed(3)},
                  composite: {aggregate.composite_signal.toFixed(3)}.
                </p>
                {verdict?.scenarios && (
                  <ul className="mt-2 space-y-1">
                    {verdict.scenarios.map(scenario => (
                      <li key={scenario.name}>
                        {scenario.name}: {(scenario.score * 100).toFixed(1)}% internal scenario weight
                      </li>
                    ))}
                  </ul>
                )}
              </details>
            </>
          )}
        </div>
      </div>

    </motion.div>
  )
}
