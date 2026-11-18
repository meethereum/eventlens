/**
 * BaselineComparison — "Compare with plain LLM" toggle panel.
 *
 * Shows a side-by-side of the EventLens verdict vs a context-free LLM answer.
 * Rendered below the VerdictPanel when the toggle is on.
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Cpu, ChevronDown, ChevronUp, Loader2, AlertTriangle } from 'lucide-react'
import { useBaseline } from '@/hooks/useBaseline'
import type { VerdictOutput } from '@/types'

interface Props {
  query: string
  verdict: VerdictOutput | null
}

export default function BaselineComparison({ query, verdict }: Props) {
  const [open, setOpen] = useState(false)
  const { state, run } = useBaseline()

  const toggle = () => {
    if (!open && !state.response && !state.loading) {
      run(query)
    }
    setOpen(o => !o)
  }

  return (
    <div className="glass-panel overflow-hidden">
      {/* Toggle header */}
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-surface-3 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-accent-glow" />
          <span className="text-sm font-medium text-text-secondary">
            Compare with plain LLM
          </span>
          <span className="text-2xs text-text-muted border border-border px-1.5 py-0.5 rounded font-mono">
            stretch
          </span>
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-text-muted" />
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="border-t border-border p-5">
              <p className="text-xs text-text-muted mb-4 leading-relaxed">
                The same question asked to the LLM with <strong>no card context</strong> — no FRED data, no EDGAR, no sector analysis.
                This shows what the model knows from training alone.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* EventLens side */}
                <div className="glass-panel p-4 border-accent/20">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-accent" />
                    <span className="text-xs font-semibold text-accent-glow">EventLens</span>
                    <span className="text-2xs text-text-muted">(10 cards + math)</span>
                  </div>
                  {verdict ? (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-text-primary">{verdict.headline}</p>
                      <p className="text-xs text-text-secondary leading-relaxed">{verdict.summary}</p>
                    </div>
                  ) : (
                    <p className="text-xs text-text-muted italic">Analysis not yet complete.</p>
                  )}
                </div>

                {/* Plain LLM side */}
                <div className="glass-panel p-4 border-neutral/20">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-neutral" />
                    <span className="text-xs font-semibold text-text-secondary">Plain LLM</span>
                    {state.model_used && (
                      <span className="text-2xs text-text-muted font-mono truncate max-w-[120px]">
                        {state.model_used}
                      </span>
                    )}
                  </div>

                  {state.loading && (
                    <div className="flex items-center gap-2 text-xs text-text-muted">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Asking LLM…</span>
                    </div>
                  )}

                  {state.error && !state.loading && (
                    <div className="flex items-start gap-2 text-xs text-amber">
                      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                      <span>{state.error}</span>
                    </div>
                  )}

                  {state.response && !state.loading && (
                    <p className="text-xs text-text-secondary leading-relaxed whitespace-pre-wrap">
                      {state.response}
                    </p>
                  )}

                  {state.is_fallback && state.response && (
                    <p className="text-2xs text-amber mt-2 italic">
                      Note: LLM unavailable — showing fallback message.
                    </p>
                  )}
                </div>
              </div>

              <p className="text-2xs text-text-muted mt-4 leading-relaxed">
                EventLens uses the same model but grounds its answer in {Object.keys({}).length} quantitative
                analysis cards with real FRED, EDGAR, and market data. The plain LLM has no access to current data.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
