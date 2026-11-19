import { useEffect, useRef, useState } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  SlidersHorizontal,
  Sparkles,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Info,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  runId: string
}

interface FactorImpact {
  card_id: string
  factor: string
  signal_change: number
}

interface SimulationResult {
  run_id: string
  baseline: {
    composite_signal: number
    evidence_strength: number
    coverage: number
    scenario_names: string[]
    scenario_scores: number[]
  }
  scenario: {
    composite_signal: number
    evidence_strength: number
    coverage: number
    scenario_names: string[]
    scenario_scores: number[]
    scenario_ci_low?: number[]
    scenario_ci_high?: number[]
    card_contributions?: Record<string, number>
    factor_impacts: FactorImpact[]
  }
  presentation: {
    headline: string
    summary: string
    change_summary: string
    confidence_label: string
    drivers: Array<{
      name: string
      direction: string
      weight: number
      factor?: string
      card_id?: string
      signal_change?: number
    }>
  }
  composite_change: number
  scenario_score_changes: number[]
  disclaimer: string
}

interface ScenarioExplanation {
  explanation: string
  citations: Array<{ number: number; title: string; url: string }>
  cached: boolean
  used_llm: boolean
}

const SLIDERS = [
  {
    key: 'oil_pct',
    label: 'Oil Price Change',
    short: 'Oil',
    factor: 'Oil prices',
    min: -20,
    max: 20,
    step: 1,
    unit: '%',
    desc: 'Impacts operating costs, fuel, and energy producer revenues',
  },
  {
    key: 'usd_pct',
    label: 'US Dollar (DXY) Change',
    short: 'USD',
    factor: 'US dollar strength',
    min: -20,
    max: 20,
    step: 1,
    unit: '%',
    desc: 'Impacts overseas revenue translation and export competitiveness',
  },
  {
    key: 'yield_bp',
    label: '10-Year Yield Change',
    short: '10Y Yield',
    factor: 'Interest rates and inflation',
    min: -100,
    max: 100,
    step: 5,
    unit: ' bp',
    desc: 'Affects borrowing costs, bank net interest margins, and valuation multiples',
  },
  {
    key: 'vix_pct',
    label: 'Market Volatility (VIX)',
    short: 'VIX',
    factor: 'Market regime',
    min: -30,
    max: 30,
    step: 1,
    unit: '%',
    desc: 'Measures macro fear and broader risk appetite across equities',
  },
] as const

type OverrideKey = typeof SLIDERS[number]['key']
type Overrides = Record<OverrideKey, number>

const initialOverrides: Overrides = { oil_pct: 0, usd_pct: 0, yield_bp: 0, vix_pct: 0 }

export default function WhatIfPanel({ runId }: Props) {
  const [overrides, setOverrides] = useState<Overrides>(initialOverrides)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [explanation, setExplanation] = useState<ScenarioExplanation | null>(null)
  const [explanationLoading, setExplanationLoading] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const explanationCache = useRef(new Map<string, ScenarioExplanation>())
  const explanationController = useRef<AbortController | null>(null)

  const hasOverrides = Object.values(overrides).some(val => val !== 0)

  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setLoading(true)
      setError('')
      try {
        const response = await fetch('/api/simulate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ run_id: runId, ...overrides }),
          signal: controller.signal,
        })
        if (!response.ok) throw new Error(`Scenario calculation failed (${response.status})`)
        setResult(await response.json())
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setError((err as Error).message || 'Scenario calculation failed')
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }, 250)

    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [runId, overrides])

  const explainScenario = async () => {
    const key = `${runId}:${SLIDERS.map(({ key }) => `${key}=${overrides[key]}`).join('&')}`
    const cached = explanationCache.current.get(key)
    if (cached) {
      setExplanation({ ...cached, cached: true })
      return
    }

    setExplanationLoading(true)
    setError('')
    const controller = new AbortController()
    explanationController.current = controller
    try {
      const response = await fetch('/api/simulate/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: runId, ...overrides }),
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`Could not explain scenario (${response.status})`)
      const data: ScenarioExplanation = await response.json()
      explanationCache.current.set(key, data)
      setExplanation(data)
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError((err as Error).message || 'Could not explain scenario')
      }
    } finally {
      if (explanationController.current === controller) {
        explanationController.current = null
        setExplanationLoading(false)
      }
    }
  }

  useEffect(() => {
    explanationController.current?.abort()
    explanationController.current = null
    setExplanation(null)
    setExplanationLoading(false)
    return () => explanationController.current?.abort()
  }, [runId, overrides])

  const handleReset = () => {
    setOverrides(initialOverrides)
  }

  // Baseline vs Scenario Metrics
  const baseSignal = result?.baseline?.composite_signal ?? 0
  const simSignal = result?.scenario?.composite_signal ?? 0
  const deltaSignal = result?.composite_change ?? (simSignal - baseSignal)

  // Map -1 to 1 to 0% to 100% position on the spectrum bar
  const basePos = Math.min(100, Math.max(0, ((baseSignal + 1) / 2) * 100))
  const simPos = Math.min(100, Math.max(0, ((simSignal + 1) / 2) * 100))

  const scenarioMeta = [
    {
      name: 'Tailwind-dominant',
      label: 'Tailwind Outlook',
      color: '#10b981',
      bgClass: 'bg-tailwind/10 text-tailwind border-tailwind/20',
      barClass: 'bg-emerald-500',
      icon: TrendingUp,
    },
    {
      name: 'Mixed',
      label: 'Mixed / Rangebound',
      color: '#f59e0b',
      bgClass: 'bg-amber/10 text-amber border-amber/20',
      barClass: 'bg-amber-400',
      icon: Minus,
    },
    {
      name: 'Headwind-dominant',
      label: 'Headwind Outlook',
      color: '#ef4444',
      bgClass: 'bg-headwind/10 text-headwind border-headwind/20',
      barClass: 'bg-rose-500',
      icon: TrendingDown,
    },
  ]

  return (
    <section className="glass-panel p-6 space-y-6">
      {/* Header with Title and Reset */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-5 h-5 text-accent-glow" />
            <h2 className="text-lg font-semibold text-text-primary">
              What-If Sensitivity Simulator
            </h2>
          </div>
          <p className="text-xs text-text-muted mt-1">
            Stress-test how macroeconomic factor changes shift the Dirichlet scenario distribution and composite signal.
          </p>
        </div>

        {hasOverrides && (
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-surface-2 text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset to Baseline
          </button>
        )}
      </div>

      {/* Sliders Grid */}
      <div className="grid gap-4 sm:grid-cols-2">
        {SLIDERS.map(slider => {
          const val = overrides[slider.key]
          const isShifted = val !== 0
          return (
            <div
              key={slider.key}
              className={cn(
                'rounded-xl border p-4 transition-all duration-200',
                isShifted
                  ? 'bg-surface-3/80 border-accent/30 shadow-sm'
                  : 'bg-surface-2/60 border-border hover:border-border/80',
              )}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className="text-sm font-medium text-text-primary">
                  {slider.label}
                </span>
                <span
                  className={cn(
                    'font-mono text-xs px-2 py-0.5 rounded-md font-semibold transition-colors',
                    isShifted
                      ? val > 0
                        ? 'bg-tailwind-dim text-tailwind border border-tailwind/20'
                        : 'bg-headwind-dim text-headwind border border-headwind/20'
                      : 'bg-surface-3 text-text-muted border border-border',
                  )}
                >
                  {val > 0 ? '+' : ''}
                  {val}
                  {slider.unit}
                </span>
              </div>

              <div className="flex items-center justify-between text-2xs text-text-muted mb-2">
                <span>Evidence factor: {slider.factor}</span>
                <span>{isShifted ? 'Active override' : 'Baseline (0)'}</span>
              </div>

              <input
                type="range"
                min={slider.min}
                max={slider.max}
                step={slider.step}
                value={val}
                onChange={event =>
                  setOverrides(current => ({
                    ...current,
                    [slider.key]: Number(event.target.value),
                  }))
                }
                className="w-full accent-accent-glow cursor-pointer h-1.5 bg-surface-3 rounded-lg"
                aria-label={slider.label}
              />

              <div className="flex justify-between text-2xs text-text-muted font-mono mt-1">
                <span>{slider.min}{slider.unit}</span>
                <span>0</span>
                <span>+{slider.max}{slider.unit}</span>
              </div>
            </div>
          )
        })}
      </div>

      {error && (
        <div role="alert" className="p-3 text-xs text-headwind bg-headwind-dim border border-headwind/20 rounded-lg">
          {error}
        </div>
      )}

      {/* Main Results View */}
      {result && (
        <div className="space-y-5 pt-2">
          {/* Overall composite signal */}
          <div className="rounded-xl border border-border bg-surface-2 p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                  Overall Composite Signal
                </span>
                <div className="flex items-baseline gap-3 mt-1">
                  <span className="text-2xl font-mono font-bold text-text-primary">
                    {simSignal > 0 ? '+' : ''}
                    {simSignal.toFixed(3)}
                  </span>
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className="text-text-muted">vs baseline</span>
                    <span className="font-mono text-text-secondary">
                      {baseSignal > 0 ? '+' : ''}
                      {baseSignal.toFixed(3)}
                    </span>
                    <span
                      className={cn(
                        'px-1.5 py-0.5 rounded font-mono font-semibold text-xs ml-1',
                        Math.abs(deltaSignal) < 0.005
                          ? 'bg-neutral/10 text-neutral'
                          : deltaSignal > 0
                            ? 'bg-tailwind-dim text-tailwind'
                            : 'bg-headwind-dim text-headwind',
                      )}
                    >
                      {deltaSignal > 0 ? '+' : ''}
                      {deltaSignal.toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-right">
                <span className="text-xs text-text-muted">Evidence Decisiveness</span>
                <div className="text-sm font-semibold text-text-primary mt-0.5">
                  {result.presentation.confidence_label} Confidence
                </div>
              </div>
            </div>

            {/* Visual Spectrum Bar from Headwind (-1) to Neutral (0) to Tailwind (+1) */}
            <div className="space-y-1.5 pt-1">
              <div className="relative h-2.5 w-full rounded-full bg-gradient-to-r from-rose-500/40 via-amber-400/40 to-emerald-500/40 border border-border">
                {/* Center marker */}
                <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-text-muted/40" />

                {/* Baseline needle */}
                <div
                  className="absolute -top-1 w-2 h-4.5 bg-text-muted rounded-full shadow-md -translate-x-1/2 border border-black/40"
                  style={{ left: `${basePos}%` }}
                  title={`Baseline: ${baseSignal.toFixed(2)}`}
                />

                {/* Simulated needle */}
                <div
                  className="absolute -top-1.5 w-3.5 h-5.5 bg-accent-glow rounded-full shadow-lg -translate-x-1/2 border-2 border-white ring-2 ring-accent/30"
                  style={{ left: `${simPos}%` }}
                  title={`Simulated: ${simSignal.toFixed(2)}`}
                />
              </div>

              <div className="flex justify-between text-2xs text-text-muted font-medium">
                <span className="text-rose-400">-1.0 Headwinds</span>
                <span>0.0 Neutral</span>
                <span className="text-emerald-400">+1.0 Tailwinds</span>
              </div>
            </div>
          </div>

          {/* 3 Outcome Probabilities Grid */}
          <div className="space-y-2.5">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              Scenario Probability Shifts (Dirichlet Posterior)
            </h3>

            <div className="grid gap-3 sm:grid-cols-3">
              {scenarioMeta.map((meta, index) => {
                const baseProb = (result.baseline.scenario_scores[index] ?? 0) * 100
                const simProb = (result.scenario.scenario_scores[index] ?? 0) * 100
                const change = result.scenario_score_changes?.[index] !== undefined
                  ? result.scenario_score_changes[index] * 100
                  : simProb - baseProb
                const Icon = meta.icon

                return (
                  <div
                    key={meta.name}
                    className="rounded-xl border border-border bg-surface-2 p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <Icon className="w-4 h-4" style={{ color: meta.color }} />
                        <span className="text-xs font-medium text-text-primary">
                          {meta.name.replace('-dominant', '')}
                        </span>
                      </div>
                      <span
                        className={cn(
                          'text-2xs font-mono font-semibold px-1.5 py-0.5 rounded',
                          Math.abs(change) < 0.1
                            ? 'text-text-muted bg-surface-3'
                            : change > 0
                              ? 'text-tailwind bg-tailwind-dim'
                              : 'text-headwind bg-headwind-dim',
                        )}
                      >
                        {change > 0 ? '+' : ''}
                        {change.toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between">
                      <span className="text-xl font-mono font-bold text-text-primary">
                        {simProb.toFixed(1)}%
                      </span>
                      <span className="text-2xs text-text-muted font-mono">
                        base: {baseProb.toFixed(1)}%
                      </span>
                    </div>

                    {/* Comparative Dual Progress Bar */}
                    <div className="space-y-1">
                      <div className="h-1.5 w-full bg-surface-3 rounded-full overflow-hidden">
                        <div
                          className={cn('h-full rounded-full transition-all duration-300', meta.barClass)}
                          style={{ width: `${Math.min(100, Math.max(0, simProb))}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Qualitative Synthesis & Drivers */}
          <div className="rounded-xl border border-border bg-surface-2 p-5 space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-text-primary">
                  {loading ? 'Re-evaluating scenario...' : result.presentation.headline}
                </span>
              </div>
              <p className="text-xs text-text-secondary mt-1.5 leading-relaxed">
                {result.presentation.summary}
              </p>
              <p className="text-xs text-accent-glow font-medium mt-1">
                {result.presentation.change_summary}
              </p>
            </div>

            {/* Active Factor Transmission Drivers */}
            {result.presentation.drivers.length > 0 && (
              <div className="border-t border-border/60 pt-3 space-y-2">
                <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                  Active Sensitivity Channels
                </span>
                <div className="grid gap-2 sm:grid-cols-2">
                  {result.presentation.drivers.map(driver => (
                    <div
                      key={driver.name}
                      className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-surface-3 border border-border/50"
                    >
                      <span className="font-medium text-text-secondary">{driver.name}</span>
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            'text-2xs px-2 py-0.5 rounded font-medium',
                            driver.direction === 'supports'
                              ? 'bg-tailwind-dim text-tailwind'
                              : 'bg-headwind-dim text-headwind',
                          )}
                        >
                          {driver.direction}
                        </span>
                        <span className="font-mono text-2xs text-text-muted">
                          {driver.weight}% impact
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Explain this Scenario Action */}
            <div className="border-t border-border/60 pt-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h4 className="text-xs font-semibold text-text-primary flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-accent-glow" />
                    AI Scenario Comparison & Synthesis
                  </h4>
                  <p className="text-2xs text-text-muted mt-0.5">
                    Generate an LLM research analyst summary comparing this stressed scenario against baseline.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={explainScenario}
                  disabled={explanationLoading}
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg border border-accent/40 bg-accent/15 text-accent-glow hover:bg-accent/25 hover:border-accent transition-all shadow-sm disabled:opacity-50"
                >
                  <Sparkles className={cn("w-3.5 h-3.5", explanationLoading && "animate-spin")} />
                  {explanationLoading ? 'Generating AI Comparison...' : 'Compare Scenarios with AI'}
                </button>
              </div>

              {explanation && (
                <div className="mt-3.5 rounded-xl border border-accent/20 bg-surface-3/70 p-4 space-y-3 shadow-sm">
                  <div className="flex items-center justify-between border-b border-border/60 pb-2">
                    <span className="text-xs font-semibold text-accent-glow flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      Analyst Scenario Comparison
                    </span>
                    <span
                      className={cn(
                        "text-2xs px-2 py-0.5 rounded-full font-medium border",
                        explanation.used_llm
                          ? "bg-tailwind-dim text-tailwind border-tailwind/20"
                          : "bg-surface-2 text-text-muted border-border"
                      )}
                    >
                      {explanation.used_llm ? "LLM Powered" : "Template"}
                      {explanation.cached && " (cached)"}
                    </span>
                  </div>

                  <p className="text-xs text-text-secondary leading-relaxed font-normal">
                    {explanation.explanation}
                  </p>

                  {explanation.citations.length > 0 && (
                    <div className="border-t border-border/50 pt-2.5 space-y-1.5">
                      <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                        Cited Macro Factor Sources:
                      </span>
                      <ul className="grid gap-1 sm:grid-cols-2">
                        {explanation.citations.map(cit => (
                          <li key={cit.number} className="text-xs">
                            <a
                              href={cit.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-accent-glow hover:underline text-2xs p-1.5 rounded bg-surface-2/60 border border-border/40 w-full"
                            >
                              <span className="font-semibold font-mono">[{cit.number}]</span>
                              <span className="truncate flex-1">{cit.title}</span>
                              <ExternalLink className="w-3 h-3 shrink-0 opacity-70" />
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Mathematical Collapsible Details */}
          <div className="border-t border-border/60 pt-2">
            <button
              type="button"
              onClick={() => setShowDetails(prev => !prev)}
              className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
            >
              <Info className="w-3.5 h-3.5" />
              <span>How are these sensitivity calculations computed?</span>
              {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showDetails && (
              <div className="mt-3 text-xs text-text-muted space-y-2 bg-surface-2 p-3.5 rounded-lg border border-border">
                <p>
                  The simulator applies an illustrative bounded adjustment (&plusmn;0.25 max) directly to the evidence
                  evidence linked to the adjusted factors, taking into account each company's historical factor correlation direction (direction = sign(&rho;)).
                </p>
                <p>
                  It then recomputes the Dirichlet posterior distribution across the 3 scenarios ($\alpha = 1$)
                  and recalculates the normalized Shannon entropy evidence strength:
                </p>
                <div className="font-mono text-2xs bg-surface-3 p-2 rounded text-text-secondary space-y-0.5">
                  <div>Baseline: {result.scenario.scenario_names.map((n, i) => `${n.replace('-dominant', '')}: ${(result.baseline.scenario_scores[i] * 100).toFixed(1)}%`).join(' | ')}</div>
                  <div>Scenario: {result.scenario.scenario_names.map((n, i) => `${n.replace('-dominant', '')}: ${(result.scenario.scenario_scores[i] * 100).toFixed(1)}%`).join(' | ')}</div>
                </div>
              </div>
            )}
          </div>

          <p className="text-2xs text-text-muted italic text-center">
            {result.disclaimer}
          </p>
        </div>
      )}
    </section>
  )
}
