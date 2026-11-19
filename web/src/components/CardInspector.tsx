import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn, signalColors, formatDate } from '@/lib/utils'
import { cardDisplayName, cardDescription } from '@/lib/companies'
import type { CardOutput } from '@/types'
import ReactECharts from 'echarts-for-react'

interface Props {
  card: CardOutput | null
  runId: string | null
  onClose: () => void
}

type Tab = 'evidence' | 'reasoning' | 'sources'

interface UnusualDay {
  date: string
  adjusted_price: number
  daily_percentage_move: number
  robust_score: number
}

interface DayExplanation {
  explanation: string
  classification: string
  citations: Array<{ number: number; title: string; url: string; date?: string }>
  cached: boolean
  used_llm: boolean
}

export default function CardInspector({ card, runId, onClose }: Props) {
  const [tab, setTab] = useState<Tab>('evidence')
  const [unusualDays, setUnusualDays] = useState<UnusualDay[]>([])
  const [selectedDay, setSelectedDay] = useState<string | null>(null)
  const [explanation, setExplanation] = useState<DayExplanation | null>(null)
  const [explanationLoading, setExplanationLoading] = useState(false)
  const [chartError, setChartError] = useState('')
  const explanationCache = useRef(new Map<string, DayExplanation>())
  const cardId = card?.id
  const hasSeries = (card?.series.length ?? 0) > 0

  useEffect(() => {
    setUnusualDays([])
    setSelectedDay(null)
    setExplanation(null)
    setChartError('')
    if (!cardId || !runId || !hasSeries) return
    const controller = new AbortController()
    fetch(`/api/cards/${cardId}/unusual-days?run_id=${encodeURIComponent(runId)}`, {
      signal: controller.signal,
    })
      .then(async response => {
        if (!response.ok) throw new Error(`Could not find unusual days (${response.status})`)
        return response.json()
      })
      .then(data => setUnusualDays(data.days))
      .catch(err => {
        if (err.name !== 'AbortError') setChartError(err.message || 'Could not load chart markers')
      })
    return () => controller.abort()
  }, [cardId, hasSeries, runId])

  const explainDay = async (eventDate: string) => {
    if (!card || !runId) return
    setSelectedDay(eventDate)
    const key = `${runId}:${card.id}:${eventDate}`
    const cached = explanationCache.current.get(key)
    if (cached) {
      setExplanation({ ...cached, cached: true })
      return
    }
    setExplanation(null)
    setExplanationLoading(true)
    setChartError('')
    try {
      const response = await fetch('/api/explain-day', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: runId, card_id: card.id, event_date: eventDate }),
      })
      if (!response.ok) throw new Error(`Could not explain selected day (${response.status})`)
      const data: DayExplanation = await response.json()
      explanationCache.current.set(key, data)
      setExplanation(data)
    } catch (err) {
      setChartError((err as Error).message || 'Could not explain selected day')
    } finally {
      setExplanationLoading(false)
    }
  }

  // Close on Esc
  useEffect(() => {
    if (!card) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [card, onClose])

  // Reset tab when card changes
  useEffect(() => { setTab('evidence') }, [card?.id])

  const colors = card ? signalColors(card.label) : signalColors('neutral')

  return (
    <AnimatePresence>
      {card && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          />

          {/* Drawer */}
          <motion.div
            key="drawer"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-2xl flex flex-col bg-surface-1 border-l border-border shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
              <div className="flex items-center gap-3 min-w-0">
                <div className="min-w-0">
                  <h2 className="text-base font-semibold text-text-primary truncate">
                    {cardDisplayName(card.id)}
                  </h2>
                  <div className="text-xs text-text-muted mt-0.5">
                    {cardDescription(card.id)} · {card.latency_ms}ms
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={cn(
                  'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
                  colors.badge,
                )}>
                  {card.label === 'tailwind' && <TrendingUp className="w-3 h-3" />}
                  {card.label === 'headwind' && <TrendingDown className="w-3 h-3" />}
                  {card.label === 'neutral' && <Minus className="w-3 h-3" />}
                  {card.label}
                </span>
                <button
                  onClick={onClose}
                  className="p-1.5 rounded hover:bg-surface-3 text-text-muted hover:text-text-primary transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border px-6 shrink-0">
              {(['evidence', 'reasoning', 'sources'] as Tab[]).map(t => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={cn(
                    'px-4 py-2.5 text-xs font-medium border-b-2 -mb-px transition-colors capitalize',
                    tab === t
                      ? 'border-accent text-accent-glow'
                      : 'border-transparent text-text-muted hover:text-text-secondary',
                  )}
                >
                  {t}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto">
              {tab === 'evidence' && (
                <EvidenceTab
                  card={card}
                  colors={colors}
                  unusualDays={unusualDays}
                  onExplainDay={explainDay}
                  selectedDay={selectedDay}
                  explanation={explanation}
                  explanationLoading={explanationLoading}
                  chartError={chartError}
                />
              )}
              {tab === 'reasoning' && <ReasoningTab card={card} />}
              {tab === 'sources' && <SourcesTab card={card} />}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
// ─── Tab: Evidence ─────────────────────────────────────────────────────────

function EvidenceTab({
  card,
  colors,
  unusualDays,
  onExplainDay,
  selectedDay,
  explanation,
  explanationLoading,
  chartError,
}: {
  card: CardOutput
  colors: ReturnType<typeof signalColors>
  unusualDays: UnusualDay[]
  onExplainDay: (date: string) => void
  selectedDay: string | null
  explanation: DayExplanation | null
  explanationLoading: boolean
  chartError: string
}) {
  const chartOption = {
    backgroundColor: 'transparent',
    grid: { left: 40, right: 16, top: 16, bottom: 32 },
    xAxis: {
      type: 'category',
      data: card.series.map(d => d.t),
      axisLine: { lineStyle: { color: '#1f2937' } },
      axisLabel: { color: '#475569', fontSize: 10, interval: Math.floor(card.series.length / 5) },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#475569', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1f2937', type: 'dashed' } },
    },
    series: [{
      type: 'line',
      data: card.series.map(d => d.v),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: colors.hex, width: 2 },
      areaStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: colors.hex + '33' },
            { offset: 1, color: colors.hex + '00' },
          ]},
      },
      markPoint: {
        symbol: 'pin',
        symbolSize: 36,
        label: { formatter: '!', color: '#ffffff', fontWeight: 'bold' },
        itemStyle: { color: '#f59e0b' },
        data: unusualDays.map(day => ({
          coord: [day.date, day.adjusted_price],
          name: day.date,
          value: 'Unusual',
        })),
      },
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#141820',
      borderColor: '#1f2937',
      textStyle: { color: '#f1f5f9', fontSize: 11, fontFamily: 'JetBrains Mono' },
    },
  }
  const chartEvents = {
    click: (params: { componentType?: string; name?: string }) => {
      if (params.componentType === 'markPoint' && params.name) onExplainDay(params.name)
    },
  }

  return (
    <div className="p-6 space-y-6">
      {/* Chart */}
      {card.series.length > 0 && (
        <div>
          <h3 className="text-xs font-medium text-text-secondary mb-3">
            {card.id === 'C5' ? 'Adjusted closing price' : 'Time Series'}
          </h3>
          <div className="glass-panel p-2">
            <ReactECharts option={chartOption} onEvents={chartEvents} style={{ height: 200 }} />
          </div>
          <p className="mt-2 text-xs text-text-muted">
            {unusualDays.length
              ? 'Click an amber marker to inspect an unusually large move in this series.'
              : 'No unusually large daily moves were detected in this series.'}
          </p>
          {selectedDay && (
            <div className="mt-3 rounded-lg border border-border bg-surface-2 p-4">
              <div className="text-xs font-medium text-text-primary">
                Selected day: {selectedDay}
              </div>
              {explanationLoading && <p className="mt-2 text-sm text-text-muted">Preparing explanation…</p>}
              {explanation && (
                <>
                  <p className="mt-2 text-sm leading-relaxed text-text-secondary">{explanation.explanation}</p>
                  <p className="mt-2 text-xs font-medium text-text-muted">
                    Classification: {explanation.classification.replace(/_/g, ' ')}
                  </p>
                  {explanation.citations.length > 0 && (
                    <ol className="mt-2 space-y-1">
                      {explanation.citations.map(citation => (
                        <li key={citation.number} className="text-xs">
                          <a href={citation.url} target="_blank" rel="noopener noreferrer" className="text-accent-glow hover:underline">
                            [{citation.number}] {citation.title}{citation.date ? ` · ${citation.date}` : ''}
                          </a>
                        </li>
                      ))}
                    </ol>
                  )}
                  <p className="mt-2 text-xs text-text-muted">
                    {explanation.cached ? 'Cached explanation.' : explanation.used_llm ? 'Evidence-grounded explanation.' : 'Cited template explanation.'}
                  </p>
                </>
              )}
            </div>
          )}
          {chartError && <p role="alert" className="mt-2 text-xs text-headwind">{chartError}</p>}
        </div>
      )}

      {/* Metric table */}
      <div>
        <h3 className="text-xs font-medium text-text-secondary mb-3">Metrics</h3>
        <div className="glass-panel overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-3 text-text-muted font-medium">Metric</th>
                <th className="text-right p-3 text-text-muted font-medium font-mono">Value</th>
                <th className="text-left p-3 text-text-muted font-medium">Unit</th>
              </tr>
            </thead>
            <tbody>
              {card.metrics.map((m, i) => (
                <tr key={i} className="border-b border-border/50 last:border-0">
                  <td className="p-3 text-text-secondary">{m.name}</td>
                  <td className="p-3 text-right font-mono text-text-primary tabular-nums">
                    {m.value !== null && m.value !== undefined ? String(m.value) : '—'}
                  </td>
                  <td className="p-3 text-text-muted">{m.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warnings */}
      {card.warnings.length > 0 && (
        <div className="space-y-2">
          {card.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-amber bg-amber-muted border border-amber/20 rounded px-3 py-2">
              <span>⚠</span> {w}
            </div>
          ))}
        </div>
      )}
      <details className="rounded-lg border border-border px-4 py-3 text-xs text-text-muted">
        <summary className="cursor-pointer">How was this calculated?</summary>
        <p className="mt-2">
          The chart uses the recorded {card.id === 'C5' ? 'adjusted closing price' : 'time series'}.
          Unusual days are selected from daily percentage moves using their median and median absolute
          deviation. The explanation uses only the dated evidence and sources listed above.
        </p>
      </details>
    </div>
  )
}

// ─── Tab: Reasoning ────────────────────────────────────────────────────────

function ReasoningTab({ card }: { card: CardOutput }) {
  return (
    <div className="p-6 space-y-4">
      <p className="text-xs text-text-muted">
        Template-generated reasoning — constructed from measured values, not LLM output.
      </p>
      <ol className="space-y-3">
        {card.reasoning.map((step, i) => (
          <li key={i} className="flex gap-3">
            <span className="shrink-0 w-5 h-5 rounded-full bg-surface-3 border border-border text-2xs font-mono text-text-muted flex items-center justify-center mt-0.5">
              {i + 1}
            </span>
            <p className="text-sm text-text-secondary leading-relaxed">{step}</p>
          </li>
        ))}
      </ol>
    </div>
  )
}

// ─── Tab: Sources ──────────────────────────────────────────────────────────

function SourcesTab({ card }: { card: CardOutput }) {
  return (
    <div className="p-6 space-y-3">
      {card.sources.length === 0 && (
        <p className="text-sm text-text-muted">No sources recorded.</p>
      )}
      {card.sources.map((src, i) => (
        <div key={i} className="glass-panel p-3 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-sm text-text-primary font-medium truncate">{src.name}</div>
            <div className="text-xs text-text-muted font-mono mt-0.5">
              Retrieved: {formatDate(src.retrieved_at)}
            </div>
          </div>
          {src.url && (
            <a
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 p-1.5 rounded hover:bg-surface-3 text-text-muted hover:text-accent-glow transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      ))}
    </div>
  )
}
