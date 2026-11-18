import { useEffect, useState } from 'react'
import ReactECharts from 'echarts-for-react'

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
  match_reason: string
  source: { title: string; url: string }
  outcomes: {
    returns: Record<Entity, { d5: number; d20: number; d60: number }>
    series: Record<Entity, OutcomePoint[]>
  }
}

interface Props {
  ticker: string
  eventType: string
  asOf: string
  marketMood: string
}

export default function PrecedentPanel({ ticker, eventType, asOf, marketMood }: Props) {
  const [matches, setMatches] = useState<Precedent[]>([])
  const [note, setNote] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
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
        setMatches(data.matches)
        setNote(data.note)
        setError('')
      })
      .catch(err => {
        if ((err as Error).name !== 'AbortError') {
          setError((err as Error).message || 'Could not load precedents')
        }
      })
    return () => controller.abort()
  }, [ticker, eventType, asOf, marketMood])

  return (
    <section className="glass-panel p-5 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-text-primary">Similar past events</h2>
        <p className="text-sm text-text-muted mt-1">
          Earlier cases ranked by event type, company, sector, and market backdrop.
        </p>
      </div>
      {error && <p role="alert" className="text-sm text-headwind">{error}</p>}
      {matches.length === 0 && !error && (
        <p className="text-sm text-text-muted">        No verified historical precedents are available yet.</p>
      )}
      <div className="space-y-3">
        {matches.map(item => (
          <article key={item.id} className="rounded-lg border border-border bg-surface-2 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-medium text-text-primary">
                {item.ticker} · {item.event_type}
              </h3>
              <span className="text-xs text-text-muted">{item.event_date}</span>
            </div>
            <p className="mt-2 text-sm text-text-secondary">{item.summary}</p>
            <p className="mt-2 text-xs text-text-muted">Matched on: {item.match_reason}</p>
            <a
            href={item.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-block text-xs text-accent-glow hover:underline"
            >
            Source: {item.source.title}
            </a>
            <div className="mt-3 glass-panel p-2">
            <ReactECharts
              option={outcomeChartOption(item)}
              style={{ height: 190 }}
              notMerge
            />
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {([
              ['stock', item.ticker],
              ['sector', item.sector_etf],
              ['spy', 'SPY'],
            ] as const).map(([entity, label]) => (
              <div key={entity} className="rounded border border-border/70 p-2">
                <p className="text-xs font-medium text-text-secondary">{label}</p>
                <p className="mt-1 text-2xs text-text-muted">
                  5d {formatReturn(item.outcomes.returns[entity].d5)} ·
                  20d {formatReturn(item.outcomes.returns[entity].d20)} ·
                  60d {formatReturn(item.outcomes.returns[entity].d60)}
                </p>
              </div>
            ))}
            </div>
          </article>
        ))}
      </div>
      {note && <p className="text-xs text-text-muted">{note}</p>}
    </section>
  )
}

function formatReturn(value: number) {
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
}

function outcomeChartOption(item: Precedent) {
  const series = [
    { key: 'stock' as const, label: item.ticker, color: '#38bdf8' },
    { key: 'sector' as const, label: item.sector_etf, color: '#f59e0b' },
    { key: 'spy' as const, label: 'SPY', color: '#a78bfa' },
  ]
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      data: series.map(line => line.label),
      textStyle: { color: '#94a3b8', fontSize: 10 },
      top: 0,
    },
    grid: { left: 44, right: 12, top: 30, bottom: 24 },
    xAxis: {
      type: 'value',
      min: 0,
      max: 60,
      name: 'Trading days',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'Normalized to 100',
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
