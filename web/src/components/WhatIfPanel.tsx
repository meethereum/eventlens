import { useEffect, useRef, useState } from 'react'

interface Props {
  runId: string
}

interface SimulationResult {
  scenario: {
    composite_signal: number
    evidence_strength: number
    scenario_names: string[]
    scenario_scores: number[]
    factor_impacts: Array<{ card_id: string; factor: string; signal_change: number }>
  }
  presentation: {
    headline: string
    summary: string
    change_summary: string
    confidence_label: string
    drivers: Array<{ name: string; direction: string; weight: number }>
  }
  disclaimer: string
}

interface ScenarioExplanation {
  explanation: string
  citations: Array<{ number: number; title: string; url: string }>
  cached: boolean
  used_llm: boolean
}

const SLIDERS = [
  { key: 'oil_pct', label: 'Oil price change', min: -20, max: 20, step: 1, unit: '%' },
  { key: 'usd_pct', label: 'US dollar change', min: -20, max: 20, step: 1, unit: '%' },
  { key: 'yield_bp', label: '10-year yield change', min: -100, max: 100, step: 5, unit: ' bp' },
  { key: 'vix_pct', label: 'VIX change', min: -30, max: 30, step: 1, unit: '%' },
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
  const explanationCache = useRef(new Map<string, ScenarioExplanation>())
  const explanationController = useRef<AbortController | null>(null)

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
    }, 300)

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

  return (
    <section className="glass-panel p-5 space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-text-primary">What if things change?</h2>
        <p className="text-sm text-text-muted mt-1">
          Adjust one factor to see how the evidence-weighted scenarios respond.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {SLIDERS.map(slider => (
          <label key={slider.key} className="block space-y-2">
            <span className="flex justify-between gap-3 text-sm text-text-secondary">
              <span>{slider.label}</span>
              <span className="font-mono text-text-primary">
                {overrides[slider.key] > 0 ? '+' : ''}{overrides[slider.key]}{slider.unit}
              </span>
            </span>
            <input
              type="range"
              min={slider.min}
              max={slider.max}
              step={slider.step}
              value={overrides[slider.key]}
              onChange={event => setOverrides(current => ({
                ...current,
                [slider.key]: Number(event.target.value),
              }))}
              className="w-full accent-sky-400"
              aria-label={slider.label}
            />
          </label>
        ))}
      </div>

      {error && <p role="alert" className="text-sm text-headwind">{error}</p>}
      {result && (
        <div aria-live="polite" className="rounded-lg border border-border bg-surface-2 p-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div className="text-sm font-medium text-text-primary">
              {loading ? 'Updating scenario…' : result.presentation.headline}
            </div>
            <div className="text-xs text-text-muted">{result.presentation.confidence_label} confidence</div>
          </div>
          <p className="mt-2 text-sm text-text-secondary">{result.presentation.summary}</p>
          <p className="mt-1 text-sm text-text-secondary">{result.presentation.change_summary}</p>
          {result.presentation.drivers.length > 0 && (
            <div className="mt-4 space-y-3">
              <h3 className="text-xs font-medium text-text-secondary">What matters most</h3>
              {result.presentation.drivers.map(driver => (
                <div key={driver.name}>
                  <div className="mb-1 flex justify-between gap-3 text-xs">
                    <span className="text-text-secondary">{driver.name}</span>
                    <span className="text-text-muted">{driver.direction}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-surface-3">
                    <div className="h-full rounded-full bg-sky-400" style={{ width: `${driver.weight}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
          <button
            type="button"
            onClick={explainScenario}
            disabled={explanationLoading}
            className="mt-4 rounded-md border border-border px-3 py-2 text-xs text-text-secondary hover:bg-surface-3 disabled:opacity-50"
          >
            {explanationLoading ? 'Preparing explanation…' : 'Explain this scenario'}
          </button>
          {explanation && (
            <div className="mt-3 rounded-md border border-border bg-surface-3/50 p-3">
              <p className="text-sm text-text-secondary">{explanation.explanation}</p>
              {explanation.citations.length > 0 && (
                <ol className="mt-2 space-y-1">
                  {explanation.citations.map(citation => (
                    <li key={citation.number} className="text-xs">
                      <a href={citation.url} target="_blank" rel="noopener noreferrer" className="text-accent-glow hover:underline">
                        [{citation.number}] {citation.title}
                      </a>
                    </li>
                  ))}
                </ol>
              )}
              <p className="mt-2 text-2xs text-text-muted">
                {explanation.cached ? 'Cached explanation.' : explanation.used_llm ? 'Evidence-grounded explanation.' : 'Template explanation.'}
              </p>
            </div>
          )}
          <details className="mt-4 text-xs text-text-muted">
            <summary className="cursor-pointer">How was this calculated?</summary>
            <p className="mt-2">
              The simulator deterministically adjusts only the evidence cards linked to changed factors,
              then recalculates the scenario distribution. It does not fetch new data or make a model call.
            </p>
            <p className="mt-1">Internal scenario values: {result.scenario.scenario_names.map((name, index) =>
              `${name} ${(result.scenario.scenario_scores[index] * 100).toFixed(1)}%`,
            ).join(' · ')}</p>
          </details>
          <p className="mt-3 text-xs text-text-muted">{result.disclaimer}</p>
        </div>
      )}
    </section>
  )
}
