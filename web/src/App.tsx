import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import {
  FileText,
  Sliders,
  TrendingUp,
  LayoutGrid,
  Layers,
} from 'lucide-react'
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
import WhatIfPanel from '@/components/WhatIfPanel'
import PrecedentPanel from '@/components/PrecedentPanel'
import BaselineComparison from '@/components/BaselineComparison'
import Sidebar, { type TabId } from '@/components/Sidebar'
import { useAnalysis } from '@/hooks/useAnalysis'
import type { CardOutput, HealthResponse } from '@/types'
import type { SubmitPayload } from '@/components/QueryBar'
import { MOCK_HEALTH } from '@/lib/mockData'
import { cn } from '@/lib/utils'

export default function App() {
  const { state, run, reset } = useAnalysis()
  const [inspectedCard, setInspectedCard] = useState<CardOutput | null>(null)
  const [activeTab, setActiveTab] = useState<TabId>('verdict')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

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
  const c4Signal = state.cards.C4?.signal ?? 0
  const marketMood = c4Signal < -0.1 ? 'risk_off' : c4Signal > 0.1 ? 'risk_on' : 'mixed'

  const isRunning =
    state.phase !== 'idle' && state.phase !== 'done' && state.phase !== 'error'

  const handleSubmit = ({ query, ticker, as_of }: SubmitPayload) => {
    setActiveTab('verdict')
    run(query, ticker, as_of)
  }

  const handleReset = () => {
    reset()
  }

  const TABS: Array<{ id: TabId; label: string; icon: typeof FileText }> = [
    { id: 'verdict', label: 'Executive Verdict', icon: FileText },
    { id: 'simulator', label: 'What-If Lab', icon: Sliders },
    { id: 'precedents', label: 'Precedents', icon: TrendingUp },
    { id: 'cards', label: 'Cards Grid', icon: LayoutGrid },
    { id: 'all', label: 'Full Briefing', icon: Layers },
  ]

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
              <div className="max-w-screen-2xl mx-auto flex items-center justify-between gap-2 text-xs text-headwind">
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

          <main className="flex-1 max-w-screen-2xl mx-auto w-full px-4 md:px-6 pb-16 pt-4 space-y-6">
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
                >
                  {/* Two-Column Sidebar + Main Canvas Layout */}
                  <div className="flex flex-col lg:flex-row gap-6 items-start">
                    {/* Left Sidebar */}
                    <Sidebar
                      ticker={state.parsed?.ticker}
                      asOf={state.parsed?.as_of}
                      eventType={state.parsed?.event_type}
                      compositeSignal={state.aggregate?.composite_signal}
                      phase={state.phase}
                      cards={state.cards}
                      activeTab={activeTab}
                      onSelectTab={setActiveTab}
                      onCardClick={setInspectedCard}
                      collapsed={sidebarCollapsed}
                      onToggleCollapse={() => setSidebarCollapsed(c => !c)}
                    />

                    {/* Main Area */}
                    <div className="flex-1 min-w-0 w-full space-y-6">
                      <PipelineStepper
                        phase={state.phase}
                        timings={state.pipelineTimings}
                      />

                      {/* Refusal card */}
                      {refusal ? (
                        <RefusalCard
                          message={refusal.error_message ?? 'Query out of scope.'}
                          onSelectExample={handleSubmit}
                        />
                      ) : (
                        <>
                          {/* Navigation Bar atop Main Canvas */}
                          <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-2">
                            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none">
                              {TABS.map(tab => {
                                const Icon = tab.icon
                                const isActive = activeTab === tab.id
                                return (
                                  <button
                                    key={tab.id}
                                    type="button"
                                    onClick={() => setActiveTab(tab.id)}
                                    className={cn(
                                      'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0',
                                      isActive
                                        ? 'bg-accent/15 text-accent-glow border border-accent/30 shadow-sm'
                                        : 'text-text-muted hover:text-text-secondary hover:bg-surface-2',
                                    )}
                                  >
                                    <Icon className="w-3.5 h-3.5" />
                                    <span>{tab.label}</span>
                                  </button>
                                )
                              })}
                            </div>
                          </div>

                          {/* Tab 1: Executive Verdict */}
                          {(activeTab === 'verdict' || activeTab === 'all') && (
                            <section className="space-y-6">
                              {(state.aggregate ||
                                state.phase === 'synthesising' ||
                                state.phase === 'done') && (
                                <div className="space-y-5">
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

                                  {state.phase === 'done' && (
                                    <BaselineComparison
                                      query={state.query}
                                      verdict={state.verdict}
                                    />
                                  )}
                                </div>
                              )}
                            </section>
                          )}

                          {/* Tab 2: What-If Sensitivity Simulator */}
                          {(activeTab === 'simulator' || activeTab === 'all') && (
                            <section>
                              {state.phase === 'done' && state.runId && state.aggregate ? (
                                <WhatIfPanel runId={state.runId} />
                              ) : (
                                <div className="glass-panel p-8 text-center text-xs text-text-muted">
                                  What-If Lab activates once analysis synthesis completes.
                                </div>
                              )}
                            </section>
                          )}

                          {/* Tab 3: Historical Precedents */}
                          {(activeTab === 'precedents' || activeTab === 'all') && (
                            <section>
                              {state.phase === 'done' && state.parsed ? (
                                <PrecedentPanel
                                  ticker={state.parsed.ticker}
                                  eventType={state.parsed.event_type}
                                  asOf={state.parsed.as_of}
                                  marketMood={marketMood}
                                />
                              ) : (
                                <div className="glass-panel p-8 text-center text-xs text-text-muted">
                                  Historical Precedents activate once analysis synthesis completes.
                                </div>
                              )}
                            </section>
                          )}

                          {/* Tab 4: All 10 Evidence Cards Grid */}
                          {(activeTab === 'cards' || activeTab === 'all') && (
                            <section className="space-y-3">
                              {activeTab === 'all' && (
                                <h3 className="text-sm font-semibold text-text-primary px-1">
                                  All 10 Evidence Cards
                                </h3>
                              )}
                              <CardGrid
                                cards={analysisCards}
                                onCardClick={setInspectedCard}
                              />
                            </section>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </main>
        </div>
      </ErrorBoundary>

      <CardInspector
        card={inspectedCard}
        runId={state.runId}
        onClose={() => setInspectedCard(null)}
      />
    </div>
  )
}
