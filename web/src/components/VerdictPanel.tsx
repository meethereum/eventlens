import { useState } from 'react'
import { motion } from 'framer-motion'
import { Info, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { VerdictOutput, AggregateResult, CardOutput } from '@/types'
import ReactECharts from 'echarts-for-react'
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
  const [tooltipVisible, setTooltipVisible] = useState(false)

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
                      const lbl = card ? (typeof card.label === 'string' ? card.label : (card.label as any)?.value) : null
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
                    const pct = Math.round(sc.score * 100)
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
                                Most likely
                              </span>
                            )}
                          </div>
                          <span className="text-sm font-mono font-bold tabular-nums" style={{ color }}>
                            {pct}%
                          </span>
                        </div>
                        <div className="h-2 bg-surface-3 rounded-full overflow-hidden mb-1.5">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.8, ease: 'easeOut', delay: i * 0.1 }}
                            className="h-full rounded-full"
                            style={{ background: color }}
                          />
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

        {/* ── Right: charts ── */}
        <div className="space-y-4">
          {aggregate && (
            <EvidenceGauge
              strength={aggregate.evidence_strength}
              coverage={aggregate.coverage}
              composite={aggregate.composite_signal}
              tooltipVisible={tooltipVisible}
              setTooltipVisible={setTooltipVisible}
            />
          )}
          {aggregate && Object.keys(aggregate.card_contributions).length > 0 && (
            <ContributionWaterfall
              contributions={aggregate.card_contributions}
              onCardClick={onCitationClick}
            />
          )}
        </div>
      </div>

    </motion.div>
  )
}

// ─── Evidence Gauge ────────────────────────────────────────────────────────

function EvidenceGauge({
  strength, coverage, composite, tooltipVisible, setTooltipVisible,
}: {
  strength: number; coverage: number; composite: number
  tooltipVisible: boolean; setTooltipVisible: (v: boolean) => void
}) {
  const pct = Math.round(strength * 100)
  const option = {
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge',
      startAngle: 180, endAngle: 0, min: 0, max: 1,
      radius: '90%', center: ['50%', '70%'],
      pointer: { show: false },
      progress: {
        show: true, overlap: false, roundCap: true, width: 14,
        itemStyle: { color: strength > 0.5 ? '#10b981' : strength > 0.25 ? '#f59e0b' : '#6b7280' },
      },
      axisLine: { lineStyle: { width: 14, color: [[1, '#1a2030']] } },
      axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
      detail: {
        offsetCenter: [0, '-10%'], fontSize: 28,
        fontFamily: 'JetBrains Mono', fontWeight: 700, color: '#f1f5f9',
        formatter: `${pct}%`,
      },
      data: [{ value: strength }],
    }],
  }

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h4 className="text-sm font-semibold text-text-primary">How confident are we?</h4>
          <p className="text-2xs text-text-muted mt-0.5">Based on how much the data agrees</p>
        </div>
        <button
          onClick={() => setTooltipVisible(!tooltipVisible)}
          className="text-text-muted hover:text-text-secondary transition-colors p-1"
          title="How is this calculated?"
        >
          <Info className="w-4 h-4" />
        </button>
      </div>

      {tooltipVisible && (
        <div className="text-xs text-text-muted bg-surface-3 border border-border rounded-lg p-3 mb-3 leading-relaxed">
          This score measures how much the 10 data sources agree with each other.
          High = most sources point the same way. Low = mixed signals.
          <br /><br />
          <span className="text-text-secondary font-medium">Formula: </span>
          1 − H(p)/ln(3), where H is Shannon entropy of the scenario distribution.
        </div>
      )}

      <ReactECharts option={option} style={{ height: 150 }} />

      <div className="grid grid-cols-2 gap-3 mt-2">
        <div className="text-center p-2 rounded-lg bg-surface-3/50">
          <div className="text-xs text-text-muted mb-0.5">Data coverage</div>
          <div className="text-lg font-mono font-bold text-text-primary tabular-nums">
            {Math.round(coverage * 100)}%
          </div>
        </div>
        <div className="text-center p-2 rounded-lg bg-surface-3/50">
          <div className="text-xs text-text-muted mb-0.5">Net signal</div>
          <div className={cn(
            'text-lg font-mono font-bold tabular-nums',
            composite > 0.1 ? 'text-tailwind' : composite < -0.1 ? 'text-headwind' : 'text-neutral',
          )}>
            {composite > 0 ? '+' : ''}{composite.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Contribution Waterfall ────────────────────────────────────────────────

function ContributionWaterfall({
  contributions, onCardClick,
}: {
  contributions: Record<string, number>
  onCardClick: (id: string) => void
}) {
  const entries = Object.entries(contributions)
    .filter(([id]) => id !== '_refusal')
    .sort((a, b) => a[1] - b[1])

  // Use plain card names instead of C1, C2
  const labels = entries.map(([id]) => cardDisplayName(id))

  const option = {
    backgroundColor: 'transparent',
    grid: { left: 100, right: 16, top: 8, bottom: 8 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#475569', fontSize: 9, fontFamily: 'JetBrains Mono' },
      splitLine: { lineStyle: { color: '#1f2937', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#1f2937' } },
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      axisLine: { show: false }, splitLine: { show: false },
    },
    series: [{
      type: 'bar',
      data: entries.map(([, v]) => ({
        value: v,
        itemStyle: {
          color: v > 0 ? '#10b981' : '#ef4444',
          borderRadius: v > 0 ? [0, 4, 4, 0] : [4, 0, 0, 4],
        },
      })),
      barMaxWidth: 16,
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#141820', borderColor: '#1f2937',
      textStyle: { color: '#f1f5f9', fontSize: 11 },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      formatter: (params: any) => {
        const [p] = params
        const val = p.value > 0 ? `+${p.value.toFixed(3)}` : p.value.toFixed(3)
        return `${p.name}: ${val}`
      },
    },
  }

  return (
    <div className="glass-panel p-5">
      <h4 className="text-sm font-semibold text-text-primary mb-1">What's driving the signal</h4>
      <p className="text-xs text-text-muted mb-3">Green = positive contribution, red = negative</p>
      <ReactECharts
        option={option}
        style={{ height: entries.length * 26 + 20 }}
        onEvents={{
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          click: (params: any) => {
            // Map label back to card ID
            const idx = labels.indexOf(params.name)
            if (idx >= 0) onCardClick(entries[idx][0])
          },
        }}
      />
      <p className="text-2xs text-text-muted mt-2">Click a bar to see details</p>
    </div>
  )
}
