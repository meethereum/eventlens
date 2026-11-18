import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn, signalColors, formatDate } from '@/lib/utils'
import { cardDisplayName, cardDescription } from '@/lib/companies'
import type { CardOutput } from '@/types'
import ReactECharts from 'echarts-for-react'

interface Props {
  card: CardOutput | null
  onClose: () => void
}

type Tab = 'evidence' | 'reasoning' | 'math' | 'sources' | 'raw'

export default function CardInspector({ card, onClose }: Props) {
  const [tab, setTab] = useState<Tab>('evidence')

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
                  {card.label} · s={card.signal.toFixed(2)}
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
              {(['evidence', 'reasoning', 'math', 'sources', 'raw'] as Tab[]).map(t => (
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
              {tab === 'evidence' && <EvidenceTab card={card} colors={colors} />}
              {tab === 'reasoning' && <ReasoningTab card={card} />}
              {tab === 'math' && <MathTab card={card} />}
              {tab === 'sources' && <SourcesTab card={card} />}
              {tab === 'raw' && <RawTab card={card} />}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

// ─── Tab: Evidence ─────────────────────────────────────────────────────────

function EvidenceTab({ card, colors }: { card: CardOutput; colors: ReturnType<typeof signalColors> }) {
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
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#141820',
      borderColor: '#1f2937',
      textStyle: { color: '#f1f5f9', fontSize: 11, fontFamily: 'JetBrains Mono' },
    },
  }

  return (
    <div className="p-6 space-y-6">
      {/* Chart */}
      {card.series.length > 0 && (
        <div>
          <h3 className="text-xs font-medium text-text-secondary mb-3">Time Series</h3>
          <div className="glass-panel p-2">
            <ReactECharts option={chartOption} style={{ height: 200 }} />
          </div>
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

// ─── Tab: Math ─────────────────────────────────────────────────────────────

function MathTab({ card }: { card: CardOutput }) {
  if (!card.math) return (
    <div className="p-6 text-sm text-text-muted">No math detail available for this card.</div>
  )

  const { formula, inputs, contribution } = card.math

  return (
    <div className="p-6 space-y-6">
      <div>
        <h3 className="text-xs font-medium text-text-secondary mb-2">Formula</h3>
        <div className="bg-surface-3 rounded px-4 py-3 font-mono text-sm text-accent-glow border border-border">
          {formula}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-medium text-text-secondary mb-3">Inputs (actual values)</h3>
        <div className="glass-panel overflow-hidden">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-3 text-text-muted font-medium">Variable</th>
                <th className="text-right p-3 text-text-muted font-medium">Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(inputs).map(([k, v]) => (
                <tr key={k} className="border-b border-border/50 last:border-0">
                  <td className="p-3 text-text-secondary">{k}</td>
                  <td className="p-3 text-right text-text-primary tabular-nums">
                    {typeof v === 'boolean' ? String(v) : typeof v === 'number' ? v.toFixed(4) : String(v)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="text-xs font-medium text-text-secondary mb-2">Contribution to composite signal</h3>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                (contribution ?? 0) > 0 ? 'bg-tailwind' : 'bg-headwind',
              )}
              style={{ width: `${Math.abs((contribution ?? 0) * 100 / 0.3)}%` }}
            />
          </div>
          <span className={cn(
            'text-sm font-mono font-medium tabular-nums',
            (contribution ?? 0) > 0 ? 'text-tailwind' : 'text-headwind',
          )}>
            {contribution !== null && contribution !== undefined
              ? `${contribution > 0 ? '+' : ''}${contribution.toFixed(3)}`
              : '—'}
          </span>
        </div>
      </div>

      <div className="text-2xs text-text-muted border border-border rounded p-3 leading-relaxed">
        <strong className="text-text-secondary">Scoring note:</strong> Macro cards use
        s = d × tanh(z / 2) where z is the 20-day change in standard deviations, d is
        the correlation sign, and w is clipped correlation magnitude vs prior.
        Fundamental cards use rule/threshold tables. All signals are in [−1, 1].
      </div>
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

// ─── Tab: Raw JSON ─────────────────────────────────────────────────────────

function RawTab({ card }: { card: CardOutput }) {
  const json = JSON.stringify(card, null, 2)
  return (
    <div className="p-6">
      <pre className="text-2xs font-mono text-text-secondary bg-surface-3 rounded p-4 overflow-x-auto leading-relaxed border border-border max-h-[600px] overflow-y-auto">
        {json}
      </pre>
    </div>
  )
}
