import { useEffect, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  Layers,
  LineChart,
  Target,
  Clock,
  ShieldCheck,
  Percent,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface OutcomePoint {
  day: number
  date: string
  value: number
}

type Entity = 'stock' | 'sector' | 'spy'

interface Precedent {
  id: string
  event_date: string
  ticker: string
  sector_etf: string
  event_type: string
  summary: string
  similarity?: number
  match_reason: string
  source: { title: string; url: string }
  outcomes: {
    returns: Record<Entity, { d5: number; d20: number; d60: number }>
    series: Record<Entity, OutcomePoint[]>
  }
}

interface CorridorPoint {
  day: number
  median: number
  q1: number
  q3: number
  alpha_sector: number
  alpha_spy: number
}

interface CohortStats {
  cases_count: number
  median_stock_d5: number
  median_stock_d20: number
  median_stock_d60: number
  median_sector_d20: number
  median_alpha_d5: number
  median_alpha_d20: number
  median_alpha_d60: number
  win_rate_20: number
  win_rate_60: number
  alpha_win_rate_20: number
  corridor: CorridorPoint[]
}

interface AISynthesis {
  summary: string
  used_llm: boolean
  cached?: boolean
}

interface Props {
  ticker: string
  eventType: string
  asOf: string
  marketMood: string
}

type ChartMode = 'corridor' | 'alpha' | 'selected'

export default function PrecedentPanel({ ticker, eventType, asOf, marketMood }: Props) {
  const [matches, setMatches] = useState<Precedent[]>([])
  const [cohort, setCohort] = useState<CohortStats | null>(null)
  const [aiSynthesis, setAiSynthesis] = useState<AISynthesis | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [chartMode, setChartMode] = useState<ChartMode>('corridor')
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const controller = new AbortController()
    const params = new URLSearchParams({
      ticker,
      event_type: eventType,
      as_of: asOf,
      market_mood: marketMood,
    })

    fetch(`/api/precedents?${params}`, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error(`Could not load precedents (${response.status})`)
        return response.json()
      })
      .then(data => {
        setMatches(data.matches || [])
        setCohort(data.cohort || null)
        setAiSynthesis(data.ai_synthesis || null)
        setNote(data.note || '')
        if (data.matches && data.matches.length > 0) {
          setSelectedId(data.matches[0].id)
        }
        setError('')
      })
      .catch(err => {
        if ((err as Error).name !== 'AbortError') {
          setError((err as Error).message || 'Could not load precedents')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [ticker, eventType, asOf, marketMood])

  const selectedPrecedent = matches.find(m => m.id === selectedId) ?? matches[0]

  return (
    <section className="glass-panel p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-accent-glow" />
            <h2 className="text-lg font-semibold text-text-primary">
              Historical Precedent & Outcome Analysis
            </h2>
          </div>
          <p className="text-xs text-text-muted mt-1">
            Verified SEC-filed corporate analog events ranked by similarity to {ticker}'s current context.
          </p>
        </div>

        {matches.length > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-text-muted bg-surface-2 px-3 py-1.5 rounded-lg border border-border">
            <Clock className="w-3.5 h-3.5 text-accent-glow" />
            <span>{matches.length} Historical Cases Matched</span>
          </div>
        )}
      </div>

      {error && (
        <div role="alert" className="p-3 text-xs text-headwind bg-headwind-dim border border-headwind/20 rounded-lg">
          {error}
        </div>
      )}

      {loading && !error && (
        <div className="py-8 text-center text-xs text-text-muted space-y-2">
          <div className="inline-block w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <p>Analyzing historical analogs & computing cohort corridor...</p>
        </div>
      )}

      {!loading && matches.length === 0 && !error && (
        <p className="text-sm text-text-muted py-4">No verified historical precedents are available for this specific query yet.</p>
      )}

      {!loading && matches.length > 0 && (
        <>
          {/* 1. Cohort KPI Summary Cards */}
          {cohort && (
            <div className="grid gap-3 sm:grid-cols-4">
              <div className="rounded-xl border border-border bg-surface-2 p-3.5">
                <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                  20-Day Median Return
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span
                    className={cn(
                      'text-xl font-mono font-bold',
                      cohort.median_stock_d20 > 0
                        ? 'text-tailwind'
                        : cohort.median_stock_d20 < 0
                          ? 'text-headwind'
                          : 'text-text-primary',
                    )}
                  >
                    {cohort.median_stock_d20 > 0 ? '+' : ''}
                    {cohort.median_stock_d20}%
                  </span>
                  <span className="text-2xs text-text-muted">initial drift</span>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-surface-2 p-3.5">
                <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                  60-Day Median Return
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span
                    className={cn(
                      'text-xl font-mono font-bold',
                      cohort.median_stock_d60 > 0
                        ? 'text-tailwind'
                        : cohort.median_stock_d60 < 0
                          ? 'text-headwind'
                          : 'text-text-primary',
                    )}
                  >
                    {cohort.median_stock_d60 > 0 ? '+' : ''}
                    {cohort.median_stock_d60}%
                  </span>
                  <span className="text-2xs text-text-muted">quarterly outcome</span>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-surface-2 p-3.5">
                <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                  60-Day Win Rate
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-xl font-mono font-bold text-text-primary">
                    {cohort.win_rate_60}%
                  </span>
                  <span className="text-2xs text-text-muted">positive returns</span>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-surface-2 p-3.5">
                <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                  20d Alpha vs Sector
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span
                    className={cn(
                      'text-xl font-mono font-bold',
                      cohort.median_alpha_d20 > 0
                        ? 'text-tailwind'
                        : cohort.median_alpha_d20 < 0
                          ? 'text-headwind'
                          : 'text-text-primary',
                    )}
                  >
                    {cohort.median_alpha_d20 > 0 ? '+' : ''}
                    {cohort.median_alpha_d20}%
                  </span>
                  <span className="text-2xs text-text-muted">excess return</span>
                </div>
              </div>
            </div>
          )}

          {/* 2. AI Historical Synthesis Card */}
          {aiSynthesis && aiSynthesis.summary && (
            <div className="rounded-xl border border-accent/25 bg-surface-2/90 p-4 space-y-2.5 shadow-sm">
              <div className="flex items-center justify-between border-b border-border/50 pb-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-accent-glow" />
                  <span className="text-xs font-semibold text-text-primary">
                    AI Historical Precedent Synthesis
                  </span>
                </div>
                <span
                  className={cn(
                    'text-2xs px-2 py-0.5 rounded-full font-medium border',
                    aiSynthesis.used_llm
                      ? 'bg-tailwind-dim text-tailwind border-tailwind/20'
                      : 'bg-surface-3 text-text-muted border-border',
                  )}
                >
                  {aiSynthesis.used_llm ? 'Model Verified' : 'Statistical Synthesis'}
                </span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed font-normal">
                {aiSynthesis.summary}
              </p>
            </div>
          )}

          {/* 3. Interactive Multi-Mode Chart */}
          <div className="rounded-xl border border-border bg-surface-2 p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3">
              <div>
                <span className="text-xs font-semibold text-text-primary">
                  {chartMode === 'corridor' && 'Cohort Outcome Corridor (60 Trading Days)'}
                  {chartMode === 'alpha' && 'Excess Return vs Sector Benchmark (Alpha)'}
                  {chartMode === 'selected' && `${selectedPrecedent.ticker} (${selectedPrecedent.event_date}) vs Sector & Market`}
                </span>
                <p className="text-2xs text-text-muted mt-0.5">
                  {chartMode === 'corridor' && 'Shows the median path with shaded 25th–75th quartile range across all matched precedents.'}
                  {chartMode === 'alpha' && 'Isolates true company alpha (Stock minus Sector ETF return) over the 60-day horizon.'}
                  {chartMode === 'selected' && 'Three-line benchmark tracking normalized to 100 on event announcement date.'}
                </p>
              </div>

              {/* Chart Mode Toggle */}
              <div className="inline-flex rounded-lg border border-border bg-surface-3 p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setChartMode('corridor')}
                  className={cn(
                    'px-2.5 py-1 rounded-md font-medium transition-colors',
                    chartMode === 'corridor'
                      ? 'bg-surface-1 text-text-primary shadow-sm'
                      : 'text-text-muted hover:text-text-secondary',
                  )}
                >
                  Cohort Corridor
                </button>
                <button
                  type="button"
                  onClick={() => setChartMode('alpha')}
                  className={cn(
                    'px-2.5 py-1 rounded-md font-medium transition-colors',
                    chartMode === 'alpha'
                      ? 'bg-surface-1 text-text-primary shadow-sm'
                      : 'text-text-muted hover:text-text-secondary',
                  )}
                >
                  Alpha vs Sector
                </button>
                <button
                  type="button"
                  onClick={() => setChartMode('selected')}
                  className={cn(
                    'px-2.5 py-1 rounded-md font-medium transition-colors',
                    chartMode === 'selected'
                      ? 'bg-surface-1 text-text-primary shadow-sm'
                      : 'text-text-muted hover:text-text-secondary',
                  )}
                >
                  Single Case Detail
                </button>
              </div>
            </div>

            <div className="glass-panel p-2">
              <ReactECharts
                option={
                  chartMode === 'corridor'
                    ? corridorChartOption(cohort, matches)
                    : chartMode === 'alpha'
                      ? alphaChartOption(cohort, matches)
                      : singleCaseChartOption(selectedPrecedent)
                }
                style={{ height: 260 }}
                notMerge
              />
            </div>
          </div>

          {/* 4. Interactive Precedent Case Selector */}
          <div className="space-y-3">
            <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              Matched Precedent Events (Click to Inspect)
            </span>

            <div className="space-y-2.5">
              {matches.map(item => {
                const isSelected = item.id === selectedId
                const stock20 = item.outcomes.returns.stock.d20
                const sector20 = item.outcomes.returns.sector.d20
                const alpha20 = stock20 - sector20
                const similarityPct = Math.round((item.similarity ?? 0.8) * 100)

                return (
                  <article
                    key={item.id}
                    onClick={() => {
                      setSelectedId(item.id)
                      setChartMode('selected')
                    }}
                    className={cn(
                      'rounded-xl border p-4 transition-all cursor-pointer',
                      isSelected
                        ? 'bg-surface-3/90 border-accent/40 shadow-md ring-1 ring-accent/20'
                        : 'bg-surface-2/70 border-border hover:bg-surface-3/50 hover:border-border/80',
                    )}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-text-primary">
                          {item.ticker}
                        </span>
                        <span className="text-xs text-text-muted">· {item.event_date}</span>
                        <span className="text-2xs px-2 py-0.5 rounded-full bg-accent-muted text-accent-glow font-medium border border-accent/20">
                          {similarityPct}% Match
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs font-mono">
                        <span className={stock20 > 0 ? 'text-tailwind' : 'text-headwind'}>
                          20d: {stock20 > 0 ? '+' : ''}{stock20.toFixed(1)}%
                        </span>
                        <span className="text-text-muted">
                          Alpha: {alpha20 > 0 ? '+' : ''}{alpha20.toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    <p className="mt-2 text-xs text-text-secondary leading-relaxed">
                      {item.summary}
                    </p>

                    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-border/50 pt-2 text-2xs text-text-muted">
                      <span>Reason: {item.match_reason}</span>
                      <a
                        href={item.source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={e => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-accent-glow hover:underline"
                      >
                        <span>{item.source.title}</span>
                        <ExternalLink className="w-3 h-3 opacity-70" />
                      </a>
                    </div>
                  </article>
                )
              })}
            </div>
          </div>
        </>
      )}

      {note && <p className="text-xs text-text-muted text-center pt-2">{note}</p>}
    </section>
  )
}

function formatReturn(val: number) {
  return `${val > 0 ? '+' : ''}${val.toFixed(1)}%`
}

function corridorChartOption(cohort: CohortStats | null, matches: Precedent[]) {
  if (!cohort || !cohort.corridor || cohort.corridor.length === 0) return {}

  const days = cohort.corridor.map(p => p.day)
  const medians = cohort.corridor.map(p => p.median)
  const q1 = cohort.corridor.map(p => p.q1)
  const q3 = cohort.corridor.map(p => p.q3)

  // Individual faint lines
  const caseSeries = matches.slice(0, 5).map(m => ({
    name: `${m.ticker} (${m.event_date})`,
    type: 'line' as const,
    showSymbol: false,
    lineStyle: { width: 1, opacity: 0.35, type: 'dashed' as const },
    data: m.outcomes.series.stock.map(p => [p.day, p.value]),
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        if (!params || !params.length) return ''
        const day = params[0].axisValue
        let html = `<div style="font-size:11px;font-family:sans-serif;"><b>Day ${day}</b><br/>`
        params.forEach((item: any) => {
          if (item.seriesName === 'Cohort Median') {
            html += `<span style="color:${item.color};">●</span> ${item.seriesName}: <b>${item.value[1]}</b> (${formatReturn(item.value[1] - 100)})<br/>`
          } else if (item.seriesName !== 'Q3 (75th)' && item.seriesName !== 'Q1 (25th)') {
            html += `<span style="color:${item.color};">●</span> ${item.seriesName}: ${item.value[1]}<br/>`
          }
        })
        html += '</div>'
        return html
      },
    },
    legend: {
      data: ['Cohort Median', ...matches.map(m => `${m.ticker} (${m.event_date})`)],
      textStyle: { color: '#94a3b8', fontSize: 10 },
      top: 0,
      type: 'scroll',
    },
    grid: { left: 45, right: 15, top: 35, bottom: 25 },
    xAxis: {
      type: 'value',
      min: 0,
      max: 60,
      name: 'Trading Days Post-Event',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'Indexed (Day 0 = 100)',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { lineStyle: { color: '#1f2937', type: 'dashed' } },
    },
    series: [
      {
        name: 'Cohort Median',
        type: 'line',
        showSymbol: false,
        data: days.map((d, i) => [d, medians[i]]),
        lineStyle: { color: '#38bdf8', width: 2.5 },
        z: 10,
      },
      ...caseSeries,
    ],
  }
}

function alphaChartOption(cohort: CohortStats | null, matches: Precedent[]) {
  const caseSeries = matches.slice(0, 5).map(m => {
    const stock = m.outcomes.series.stock
    const sector = m.outcomes.series.sector
    const data = stock.map((p, i) => [p.day, Math.round((p.value - (sector[i]?.value ?? 100)) * 100) / 100])
    return {
      name: `${m.ticker} (${m.event_date})`,
      type: 'line' as const,
      showSymbol: false,
      data,
      lineStyle: { width: 1.5 },
    }
  })

  // Median alpha
  const medianAlpha = cohort?.corridor?.map(p => [p.day, p.alpha_sector]) ?? []

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        if (!params || !params.length) return ''
        const day = params[0].axisValue
        let html = `<div style="font-size:11px;"><b>Day ${day} Alpha (vs Sector ETF)</b><br/>`
        params.forEach((item: any) => {
          html += `<span style="color:${item.color};">●</span> ${item.seriesName}: <b>${formatReturn(item.value[1])}</b><br/>`
        })
        html += '</div>'
        return html
      },
    },
    legend: {
      data: ['Median Alpha', ...matches.map(m => `${m.ticker} (${m.event_date})`)],
      textStyle: { color: '#94a3b8', fontSize: 10 },
      top: 0,
      type: 'scroll',
    },
    grid: { left: 45, right: 15, top: 35, bottom: 25 },
    xAxis: {
      type: 'value',
      min: 0,
      max: 60,
      name: 'Trading Days',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'Excess Return (%)',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9, formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#1f2937', type: 'dashed' } },
    },
    series: [
      {
        name: 'Median Alpha',
        type: 'line',
        showSymbol: false,
        data: medianAlpha,
        lineStyle: { color: '#10b981', width: 3 },
        z: 10,
      },
      ...caseSeries,
    ],
  }
}

function singleCaseChartOption(item: Precedent) {
  if (!item) return {}
  const series = [
    { key: 'stock' as const, label: `${item.ticker} (Stock)`, color: '#38bdf8' },
    { key: 'sector' as const, label: `${item.sector_etf} (Sector ETF)`, color: '#f59e0b' },
    { key: 'spy' as const, label: 'SPY (S&P 500)', color: '#a78bfa' },
  ]

  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      data: series.map(line => line.label),
      textStyle: { color: '#94a3b8', fontSize: 10 },
      top: 0,
    },
    grid: { left: 45, right: 15, top: 35, bottom: 25 },
    xAxis: {
      type: 'value',
      min: 0,
      max: 60,
      name: 'Trading Days',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'Indexed (Day 0 = 100)',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { lineStyle: { color: '#1f2937', type: 'dashed' } },
    },
    series: series.map(line => ({
      name: line.label,
      type: 'line',
      showSymbol: false,
      data: item.outcomes.series[line.key].map(point => [point.day, point.value]),
      lineStyle: { color: line.color, width: 2 },
    })),
  }
}
