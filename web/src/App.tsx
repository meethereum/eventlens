import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import TopBar from '@/components/TopBar'
import QueryBar from '@/components/QueryBar'
import PipelineStepper from '@/components/PipelineStepper'
import CardGrid from '@/components/CardGrid'
import VerdictPanel from '@/components/VerdictPanel'
import CardInspector from '@/components/CardInspector'
import EmptyState from '@/components/EmptyState'
import DemoBanner from '@/components/DemoBanner'
import RefusalCard from '@/components/RefusalCard'
import ErrorBoundary from '@/components/ErrorBoundary'
import BaselineComparison from '@/components/BaselineComparison'
import { useAnalysis } from '@/hooks/useAnalysis'import type { CardOutput, HealthResponse } from '@/types'
import type { SubmitPayload } from '@/components/QueryBar'
import { MOCK_HEALTH } from '@/lib/mockData'

export default function App() {
  const { state, run, reset } = useAnalysis()
  const [inspectedCard, setInspectedCard] = useState<CardOutput | null>(null)

  // Dynamic page title
  useEffect(() => {
    if (state.parsed?.ticker && state.phase !== 'idle') {
      document.title = `${state.parsed.ticker} — EventLens`
    } else {
      document.title = 'EventLens — Financial Event Analysis'
    }
  }, [state.parsed?.ticker, state.phase])

  // Health check — falls back to mock if backend unreachable
  const { data: health } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('/api/health')
      if (!res.ok) throw new Error('health check failed')
      return res.json()
    },
    retry: 1,
    staleTime: 30_000,
  })

  const effectiveHealth = health ?? MOCK_HEALTH

  // Refusal card lives in cards['_refusal']
  const refusal = state.cards['_refusal']
  const analysisCards = Object.values(state.cards).filter(c => c.id !== '_refusal')

  const isRunning =
    state.phase !== 'idle' && state.phase !== 'done' && state.phase !== 'error'

  const handleSubmit = ({ query, ticker, as_of }: SubmitPayload) => {
    run(query, ticker, as_of)
  }

  const handleReset = () => {
    reset()
  }

  return (
    <div className="min-h-dvh bg-surface bg-grid relative">
      {/* Gradient vignette */}
      <div
        className="pointer-events-none fixed inset-0"
        style={{
          background:
            'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(30,58,95,0.25) 0%, transparent 100%)',
        }}
      />

      <ErrorBoundary>
        <div className="relative z-10 flex flex-col min-h-dvh">
          <TopBar health={effectiveHealth} />

          {effectiveHealth.demo_mode && (
            <DemoBanner missingKeys={effectiveHealth.missing_keys} />
          )}

          {/* Global error banner */}
          {state.phase === 'error' && state.error && (
            <div className="bg-headwind-dim border-b border-headwind/20 px-4 py-2">
              <div className="max-w-screen-xl mx-auto flex items-center justify-between gap-2 text-xs text-headwind">
                <span>⚠ {state.error}</span>
                <button
                  onClick={handleReset}
                  className="underline hover:no-underline"
                >
                  Reset
                </button>
              </div>
            </div>
          )}

          <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 md:px-6 pb-16 pt-4 space-y-6">
            <QueryBar
              onSubmit={handleSubmit}
              isRunning={isRunning}
              parsed={state.parsed}
            />

            <AnimatePresence mode="wait">
              {state.phase === 'idle' ? (
                <EmptyState key="empty" onSelect={handleSubmit} />
              ) : (
                <motion.div
                  key="analysis"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  <PipelineStepper
                    phase={state.phase}
                    timings={state.pipelineTimings}
                  />

                  {/* Refusal card — shown instead of grid when out of scope */}
                  {refusal ? (
                    <RefusalCard
                      message={refusal.error_message ?? 'Query out of scope.'}
                      onSelectExample={handleSubmit}
                    />
                  ) : (
                    <CardGrid
                      cards={analysisCards}
                      phase={state.phase}
                      onCardClick={setInspectedCard}
                      ticker={state.parsed?.ticker}
                    />
                  )}

                  {/* Verdict panel — shown once aggregate arrives */}
                  {!refusal &&
                    (state.aggregate ||
                      state.phase === 'synthesising' ||
                      state.phase === 'done') && (
                      <VerdictPanel
                        verdict={state.verdict}
                        aggregate={state.aggregate}
                        verdictStream={state.verdictStream}
                        cards={state.cards}
                        ticker={state.parsed?.ticker}
                        onCitationClick={id => {
                          const c = state.cards[id]
                          if (c) setInspectedCard(c)
                        }}
                      />
                    )}

                  {/* Baseline comparison toggle — removed per UX review */}
                </motion.div>
              )}
            </AnimatePresence>
          </main>
        </div>
      </ErrorBoundary>

      <CardInspector
        card={inspectedCard}
        onClose={() => setInspectedCard(null)}
      />
    </div>
  )
}
