import { useState, useEffect, useMemo, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  Layers,
  LineChart,
  Target,
  Clock,
  ExternalLink,
  GitCommit,
  Columns,
  Network,
  Filter,
  Calendar,
  AlertTriangle,
  FileText,
  X,
  ChevronRight,
  RefreshCw,
  Activity,
  ShieldAlert,
  Sliders,
  DollarSign,
  ArrowRight,
  Search,
  Loader2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type {
  DeepResearchTimelineOutput,
  CompanyIncidentReport,
  TimelineMilestone,
} from '@/types'
import { DEFAULT_TIMELINE_DATA } from '@/lib/defaultTimelineData'

interface Props {
  ticker?: string
  eventType?: string
  asOf?: string
  marketMood?: string
  query?: string
}

type ViewMode = 'tracks' | 'tree' | 'cohort'

const QUICK_PROMPTS = [
  {
    title: '👔 Executive Ouster & Board Coup (Intel, Starbucks, Disney, Boeing)',
    prompt:
      'A Fortune 500 board abruptly forces out the CEO amidst operational underperformance, manufacturing delays, or strategic misalignment',
  },
  {
    title: '🏦 Digital Bank Run & Liquidity Crisis (Schwab, Western Alliance, SVB)',
    prompt:
      'A major commercial bank suffers an acute digital bank run and sudden collapse due to unrealized bond portfolio losses and uninsured deposit flight',
  },
  {
    title: '⚖️ Antitrust & Monopolistic Lawsuit (Apple, Google, Microsoft, Meta)',
    prompt:
      'A dominant technology or industrial corporation faces major regulatory enforcement, DOJ antitrust lawsuit, or government antitrust trial',
  },
  {
    title: '🚨 Manufacturing Defect & Safety Grounding (Boeing, Southwest, GM)',
    prompt:
      'A major manufacturer or transportation company suffers catastrophic operational failure, safety quality defect, or regulatory grounding',
  },
  {
    title: '📉 Earnings Guidance Cliff & Restructuring (Intel, Meta, Snap, Nvidia)',
    prompt:
      'A market-leading corporation reports unexpected revenue collapse, sharp margin compression, or slashes forward guidance triggering aggressive restructuring',
  },
  {
    title: '🛡️ Global Cybersecurity Glitch & Outage (CrowdStrike, UnitedHealth, AWS)',
    prompt:
      'A major cybersecurity glitch or faulty vendor update takes down airlines, banks, and hospital IT systems worldwide',
  },
]

export default function PrecedentPanel({
  ticker = 'INTC',
  eventType = 'CEO departure',
  asOf = '',
  marketMood = 'mixed',
  query = '',
}: Props) {
  // Determine effective active prompt dynamically based on user query, ticker, or eventType
  const effectivePrompt = useMemo(() => {
    const q = (query || '').trim()
    if (q) return q
    if (ticker && eventType && eventType !== 'Corporate Incident' && eventType !== 'Incident & Crisis Forensics') {
      return `${ticker}: ${eventType}`
    }
    if (ticker && ticker !== 'UNKNOWN') {
      return `${ticker} corporate crisis and market reaction`
    }
    return DEFAULT_TIMELINE_DATA.query_prompt
  }, [query, ticker, eventType])

  // State
  const [timelineData, setTimelineData] = useState<DeepResearchTimelineOutput>(DEFAULT_TIMELINE_DATA)
  const [selectedCompanyIdx, setSelectedCompanyIdx] = useState<string>('all')
  const [viewMode, setViewMode] = useState<ViewMode>('tracks')
  const [isFetchingTimeline, setIsFetchingTimeline] = useState(false)
  const [selectedMilestone, setSelectedMilestone] = useState<{
    milestone: TimelineMilestone
    company: CompanyIncidentReport
  } | null>(null)

  // Research modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [researchPrompt, setResearchPrompt] = useState(effectivePrompt)
  const [companyCount, setCompanyCount] = useState<number>(5)
  const [isResearching, setIsResearching] = useState(false)
  const [loadingStep, setLoadingStep] = useState<string>('Analyzing scenario...')
  const [researchError, setResearchError] = useState<string | null>(null)

  // Keep research modal prompt in sync with active event
  useEffect(() => {
    if (effectivePrompt) {
      setResearchPrompt(effectivePrompt)
    }
  }, [effectivePrompt])

  // Fetch timeline data for the active event query
  const fetchTimeline = useCallback(
    async (targetPrompt: string, targetTicker?: string, targetEventType?: string) => {
      setIsFetchingTimeline(true)
      try {
        const params = new URLSearchParams()
        if (targetPrompt) params.set('prompt', targetPrompt)
        if (targetTicker) params.set('ticker', targetTicker)
        if (targetEventType) params.set('event_type', targetEventType)

        const res = await fetch(`/api/precedents/timeline?${params.toString()}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (data && data.similar_company_events?.length > 0) {
          setTimelineData(data)
          setSelectedCompanyIdx('all')
          if (data.similar_company_events[0]?.timeline?.length > 0) {
            setSelectedMilestone({
              company: data.similar_company_events[0],
              milestone: data.similar_company_events[0].timeline[0],
            })
          }
        }
      } catch (err) {
        console.warn('Failed fetching timeline for prompt, using fallback:', err)
      } finally {
        setIsFetchingTimeline(false)
      }
    },
    [],
  )

  // Re-fetch timeline whenever the event query, ticker, or event type changes
  useEffect(() => {
    fetchTimeline(effectivePrompt, ticker, eventType)
  }, [effectivePrompt, ticker, eventType, fetchTimeline])

  // Auto-select first milestone for inspector if none selected
  useEffect(() => {
    if (!selectedMilestone && timelineData?.similar_company_events?.length > 0) {
      const firstComp = timelineData.similar_company_events[0]
      if (firstComp.timeline?.length > 0) {
        setSelectedMilestone({
          company: firstComp,
          milestone: firstComp.timeline[0],
        })
      }
    }
  }, [timelineData, selectedMilestone])

  // Trigger Live Deep Research
  const handleTriggerResearch = async () => {
    if (!researchPrompt.trim()) return
    setIsResearching(true)
    setResearchError(null)

    const steps = [
      'Deconstructing scenario dimensions and causal mechanisms...',
      'Querying live corporate news & historical precedents...',
      'Extracting verified dates, triggers, causes & impacts...',
      'Mapping historical daily stock prices via yfinance...',
      'Synthesizing cross-company failure vectors and valuation drawdowns...',
    ]

    let stepIdx = 0
    const interval = setInterval(() => {
      stepIdx = (stepIdx + 1) % steps.length
      setLoadingStep(steps[stepIdx])
    }, 3200)

    try {
      const res = await fetch('/api/precedents/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: researchPrompt.trim(),
          companies: companyCount,
        }),
      })

      if (!res.ok) {
        throw new Error(`Research request failed (${res.status})`)
      }

      const data = await res.json()
      if (data && data.similar_company_events) {
        setTimelineData(data)
        setSelectedCompanyIdx('all')
        if (data.similar_company_events[0]?.timeline?.length > 0) {
          setSelectedMilestone({
            company: data.similar_company_events[0],
            milestone: data.similar_company_events[0].timeline[0],
          })
        }
      }
      setIsModalOpen(false)
    } catch (err) {
      console.error('Deep research error:', err)
      setResearchError((err as Error).message || 'Failed to complete deep research.')
    } finally {
      clearInterval(interval)
      setIsResearching(false)
    }
  }

  const companies = timelineData.similar_company_events || []
  const filteredCompanies =
    selectedCompanyIdx === 'all'
      ? companies
      : companies.filter((_, idx) => idx.toString() === selectedCompanyIdx)

  return (
    <section className="glass-panel p-6 space-y-6 relative overflow-hidden">
      {/* ── Top Header Navigation Bar ───────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-accent/15 text-accent-glow border border-accent/30 shadow-sm">
              <GitCommit className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-text-primary tracking-tight">
                Deep Research Corporate Incident & Stock Price Timeline
              </h2>
              <p className="text-xs text-text-muted">
                {timelineData.incident_category || 'Historical Corporate Crises Forensics'}
              </p>
            </div>
          </div>
        </div>

        {/* Center / Right Control Actions */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* View Mode Toggle */}
          <div className="inline-flex rounded-lg border border-border bg-surface-3 p-0.5 text-xs">
            <button
              type="button"
              onClick={() => setViewMode('tracks')}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors',
                viewMode === 'tracks'
                  ? 'bg-accent/20 text-accent-glow border border-accent/30 shadow-sm'
                  : 'text-text-muted hover:text-text-secondary',
              )}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Parallel Tracks</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('tree')}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors',
                viewMode === 'tree'
                  ? 'bg-accent/20 text-accent-glow border border-accent/30 shadow-sm'
                  : 'text-text-muted hover:text-text-secondary',
              )}
            >
              <Network className="w-3.5 h-3.5" />
              <span>LR Tree Graph</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('cohort')}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors',
                viewMode === 'cohort'
                  ? 'bg-accent/20 text-accent-glow border border-accent/30 shadow-sm'
                  : 'text-text-muted hover:text-text-secondary',
              )}
            >
              <LineChart className="w-3.5 h-3.5" />
              <span>Cohort Stats</span>
            </button>
          </div>

          {/* New Deep Research Button */}
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-accent to-blue-600 hover:from-accent-glow hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-accent/20 transition-all active:scale-95"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>New Research</span>
          </button>

          {/* Reload Button */}
          <button
            type="button"
            onClick={() => fetchTimeline(effectivePrompt, ticker, eventType)}
            disabled={isFetchingTimeline}
            title="Refresh precedents for active query"
            className="p-1.5 rounded-lg border border-border bg-surface-2 hover:bg-surface-3 text-text-muted hover:text-text-primary transition disabled:opacity-50"
          >
            <RefreshCw className={cn('w-4 h-4', isFetchingTimeline && 'animate-spin text-accent-glow')} />
          </button>
        </div>
      </div>

      {/* ── Active Prompt Context Banner ────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-surface-2/90 border border-border/80 text-xs">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-2xs uppercase tracking-wider font-semibold text-accent-glow shrink-0">
            Current Scenario Prompt:
          </span>
          {isFetchingTimeline ? (
            <span className="flex items-center gap-1.5 text-accent-glow italic font-serif">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Matching corporate precedents & stock histories for "{effectivePrompt}"...</span>
            </span>
          ) : (
            <span className="text-text-secondary truncate italic font-serif">
              "{timelineData.query_prompt}"
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-2xs text-text-muted font-mono shrink-0">
          <span>{companies.length} Major Companies Investigated</span>
          <span>·</span>
          <span>Generated: {timelineData.generated_at.slice(0, 10)}</span>
        </div>
      </div>

      {/* ── Company Filter Tabs & Phase Legend Bar ───────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3">
        <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
          <span className="text-xs font-semibold text-text-muted flex items-center gap-1 mr-1 shrink-0">
            <Filter className="w-3.5 h-3.5 text-accent-glow" />
            <span>Filter:</span>
          </span>

          <button
            type="button"
            onClick={() => setSelectedCompanyIdx('all')}
            className={cn(
              'px-3 py-1 rounded-full text-xs font-medium border shrink-0 transition-all',
              selectedCompanyIdx === 'all'
                ? 'bg-accent/20 text-accent-glow border-accent/40 font-semibold shadow-sm'
                : 'bg-surface-2 text-text-muted border-border hover:bg-surface-3 hover:text-text-secondary',
            )}
          >
            All Companies ({companies.length})
          </button>

          {companies.map((comp, idx) => {
            const isSelected = selectedCompanyIdx === idx.toString()
            const dd = comp.stock_metrics?.max_drawdown_pct
            const ddFormatted = dd !== undefined ? `${dd.toFixed(1)}%` : ''
            const tickerStr = comp.stock_ticker || 'N/A'

            return (
              <button
                key={comp.company_name + idx}
                type="button"
                onClick={() => setSelectedCompanyIdx(idx.toString())}
                className={cn(
                  'px-3 py-1 rounded-full text-xs font-medium border shrink-0 transition-all flex items-center gap-1.5',
                  isSelected
                    ? 'bg-accent/20 text-accent-glow border-accent/40 font-semibold shadow-sm'
                    : 'bg-surface-2 text-text-muted border-border hover:bg-surface-3 hover:text-text-secondary',
                )}
              >
                <span>{comp.company_name}</span>
                <span className="font-mono text-2xs font-bold text-headwind">
                  {ddFormatted}
                </span>
              </button>
            )
          })}
        </div>

        {/* Phase Color Legend */}
        <div className="hidden sm:flex items-center gap-3 text-2xs text-text-muted">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>Trigger</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            <span>Outbreak</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-400" />
            <span>Containment</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Aftermath</span>
          </span>
        </div>
      </div>

      {/* ── Main Canvas Layout: Visualizer on Left + Forensics Inspector on Right ── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Left Column (8 cols): Horizontal Parallel Tracks or LR Tree */}
        <div className="xl:col-span-8 space-y-6">
          {/* VIEW 1: Parallel Swimlane Tracks */}
          {viewMode === 'tracks' && (
            <div className="space-y-6">
              {filteredCompanies.map((comp, compIdx) => {
                const sm = comp.stock_metrics
                const tickerStr = comp.stock_ticker || 'N/A'
                const dd = sm ? sm.max_drawdown_pct : null
                const milestones = comp.timeline || []

                return (
                  <article
                    key={comp.company_name + compIdx}
                    className="rounded-2xl border border-border/80 bg-surface-2/70 backdrop-blur-sm overflow-hidden shadow-lg transition-all hover:border-border"
                  >
                    {/* Company Header Card */}
                    <div className="p-4 bg-surface-3/80 border-b border-border/70 flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-accent to-blue-700 flex items-center justify-center font-mono font-bold text-white text-xs shadow-md">
                          {tickerStr.slice(0, 4)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-sm font-bold text-text-primary">
                              {comp.company_name}
                            </h3>
                            <span className="text-2xs font-mono font-semibold px-2 py-0.5 rounded bg-surface-1 border border-border text-text-secondary">
                              {tickerStr}
                            </span>
                            {dd !== null && (
                              <span className="text-2xs font-mono font-bold px-2 py-0.5 rounded bg-headwind-dim text-headwind border border-headwind/20">
                                Peak Drop: {dd.toFixed(1)}%
                              </span>
                            )}
                          </div>
                          <p className="text-2xs text-text-muted truncate max-w-md mt-0.5">
                            {comp.incident_title} ({comp.event_timeframe})
                          </p>
                        </div>
                      </div>

                      {/* Stock Baseline vs Trough */}
                      <div className="flex items-center gap-4 text-xs font-mono">
                        <div className="text-right">
                          <span className="text-3xs uppercase text-text-muted block">
                            Baseline Price
                          </span>
                          <span className="font-semibold text-text-primary">
                            {sm ? `$${sm.baseline_price.toFixed(2)}` : 'N/A'}
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-3xs uppercase text-text-muted block">
                            Crisis Trough
                          </span>
                          <span className="font-semibold text-headwind">
                            {sm ? `$${sm.trough_price.toFixed(2)}` : 'N/A'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="p-5 space-y-4">
                      {/* Horizontal Milestone Nodes Sequence */}
                      <div className="space-y-2">
                        <span className="text-2xs uppercase tracking-wider font-semibold text-text-muted flex items-center gap-1.5">
                          <GitCommit className="w-3.5 h-3.5 text-accent-glow" />
                          <span>Event Milestone Nodes (Stock Prices Mapped Directly)</span>
                        </span>

                        <div className="flex items-center overflow-x-auto scrollbar-thin scrollbar-thumb-border pb-3 pt-1 px-1 gap-0">
                          {milestones.map((m, mIdx) => {
                            const isSelected =
                              selectedMilestone?.milestone === m &&
                              selectedMilestone?.company === comp

                            const phaseColor = getPhaseColors(m.phase)
                            const priceStr =
                              m.stock_price !== null && m.stock_price !== undefined
                                ? `$${m.stock_price.toFixed(2)}`
                                : 'N/A'
                            const chg = m.stock_change_from_baseline_pct

                            return (
                              <div key={m.date + mIdx} className="flex items-center shrink-0">
                                <div
                                  onClick={() =>
                                    setSelectedMilestone({ milestone: m, company: comp })
                                  }
                                  className={cn(
                                    'w-64 rounded-xl p-3.5 cursor-pointer shadow-md space-y-2.5 transition-all text-left border shrink-0',
                                    isSelected
                                      ? 'bg-surface-3 border-accent ring-1 ring-accent/40 scale-[1.02] shadow-accent/10 shadow-lg'
                                      : 'bg-surface-1/90 border-border/80 hover:border-accent/40 hover:bg-surface-3/60',
                                  )}
                                >
                                  {/* Phase & Date Badge */}
                                  <div className="flex items-center justify-between text-xs">
                                    <span
                                      className={cn(
                                        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-2xs font-semibold border',
                                        phaseColor.badge,
                                      )}
                                    >
                                      <span
                                        className={cn('w-1.5 h-1.5 rounded-full', phaseColor.dot)}
                                      />
                                      <span>{m.phase}</span>
                                    </span>
                                    <span className="text-2xs font-mono text-text-muted">
                                      {m.date.slice(0, 10)}
                                    </span>
                                  </div>

                                  {/* Real Stock Price Mapped onto Node */}
                                  <div className="flex items-baseline justify-between pt-1 border-t border-border/60">
                                    <span className="text-2xs text-text-muted font-medium">
                                      Closing Price:
                                    </span>
                                    <div className="flex items-center gap-1.5">
                                      <span className="font-mono font-bold text-text-primary text-xs">
                                        {priceStr}
                                      </span>
                                      {chg !== null && chg !== undefined && (
                                        <span
                                          className={cn(
                                            'text-3xs font-mono font-bold px-1.5 py-0.5 rounded border',
                                            chg < 0
                                              ? 'bg-headwind-dim text-headwind border-headwind/20'
                                              : 'bg-tailwind-dim text-tailwind border-tailwind/20',
                                          )}
                                        >
                                          {chg > 0 ? '+' : ''}
                                          {chg.toFixed(1)}%
                                        </span>
                                      )}
                                    </div>
                                  </div>

                                  {/* Event Description Snippet */}
                                  <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                                    {m.event}
                                  </p>

                                  {/* Impact Snippet */}
                                  <div className="text-2xs text-headwind truncate flex items-center gap-1 pt-0.5">
                                    <AlertTriangle className="w-3 h-3 text-headwind shrink-0" />
                                    <span className="truncate">{m.impact}</span>
                                  </div>
                                </div>

                                {/* Connecting Chevron Arrow */}
                                {mIdx < milestones.length - 1 && (
                                  <div className="flex flex-col items-center justify-center px-2 text-border">
                                    <div className="w-6 h-0.5 bg-gradient-to-r from-border via-accent/40 to-border" />
                                    <ChevronRight className="w-4 h-4 text-accent/60 -mt-2.5" />
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>

                      {/* Integrated Company Stock Trajectory Chart */}
                      {sm && sm.daily_series?.length > 0 && (
                        <div className="pt-3 border-t border-border/60 space-y-1.5">
                          <div className="flex items-center justify-between text-2xs text-text-muted font-mono">
                            <span className="flex items-center gap-1 uppercase tracking-wider font-semibold">
                              <TrendingDown className="w-3.5 h-3.5 text-accent-glow" />
                              <span>{comp.company_name} Historical Stock Curve</span>
                            </span>
                            <span>
                              {sm.baseline_date} → {sm.trough_date}
                            </span>
                          </div>

                          <div className="h-32 rounded-xl bg-surface-1/90 border border-border/60 p-2">
                            <ReactECharts
                              option={buildCompanyStockChartOption(comp)}
                              style={{ height: '100%', width: '100%' }}
                              notMerge
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </article>
                )
              })}
            </div>
          )}

          {/* VIEW 2: Left-to-Right Hierarchical Tree Graph */}
          {viewMode === 'tree' && (
            <div className="rounded-2xl border border-border/80 bg-surface-2/80 p-5 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-border/60 pb-3">
                <div className="flex items-center gap-2">
                  <Network className="w-4 h-4 text-accent-glow" />
                  <span className="text-xs font-semibold text-text-primary">
                    Interactive Left-to-Right Incident & Stock Milestone Tree
                  </span>
                </div>
                <span className="text-2xs text-text-muted">
                  Click any node to view milestone forensics
                </span>
              </div>

              <div className="h-[620px] rounded-xl bg-surface-1/90 border border-border/60 p-2">
                <ReactECharts
                  option={buildHierarchicalTreeOption(timelineData)}
                  style={{ height: '100%', width: '100%' }}
                  onEvents={{
                    click: (params: any) => {
                      const custom = params?.data?.customData
                      if (custom?.type === 'milestone') {
                        setSelectedMilestone({
                          milestone: custom.milestone,
                          company: custom.company,
                        })
                      }
                    },
                  }}
                  notMerge
                />
              </div>
            </div>
          )}

          {/* VIEW 3: Cohort Stats & Return Corridor */}
          {viewMode === 'cohort' && (
            <div className="space-y-6">
              {/* Cohort KPI Cards */}
              <div className="grid gap-3 sm:grid-cols-4">
                <div className="rounded-xl border border-border bg-surface-2 p-3.5">
                  <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                    Average Peak Drawdown
                  </span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-xl font-mono font-bold text-headwind">
                      {(
                        companies.reduce(
                          (acc, c) => acc + (c.stock_metrics?.max_drawdown_pct || 0),
                          0,
                        ) / (companies.length || 1)
                      ).toFixed(1)}
                      %
                    </span>
                    <span className="text-2xs text-text-muted">mean trough</span>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-surface-2 p-3.5">
                  <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                    Deepest Crisis Loss
                  </span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-xl font-mono font-bold text-headwind">
                      {Math.min(
                        ...companies.map(c => c.stock_metrics?.max_drawdown_pct || 0),
                      ).toFixed(1)}
                      %
                    </span>
                    <span className="text-2xs text-text-muted">max drop</span>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-surface-2 p-3.5">
                  <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                    Total Companies
                  </span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-xl font-mono font-bold text-text-primary">
                      {companies.length}
                    </span>
                    <span className="text-2xs text-text-muted">deep researched</span>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-surface-2 p-3.5">
                  <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider">
                    Milestones Analyzed
                  </span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-xl font-mono font-bold text-tailwind">
                      {companies.reduce((acc, c) => acc + (c.timeline?.length || 0), 0)}
                    </span>
                    <span className="text-2xs text-text-muted">price-mapped</span>
                  </div>
                </div>
              </div>

              {/* Multi-Company Drawdown Comparison Chart */}
              <div className="rounded-2xl border border-border/80 bg-surface-2/80 p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-border/60 pb-2">
                  <span className="text-xs font-semibold text-text-primary">
                    Multi-Company Stock Drawdown Curves Relative to Incident Baseline (100)
                  </span>
                  <span className="text-2xs text-text-muted font-mono">
                    Trading Days Normalized to Day 0
                  </span>
                </div>
                <div className="h-64 rounded-xl bg-surface-1/90 border border-border/60 p-2">
                  <ReactECharts
                    option={buildCohortComparisonOption(companies)}
                    style={{ height: '100%', width: '100%' }}
                    notMerge
                  />
                </div>
              </div>
            </div>
          )}

          {/* ── Cross-Cutting Executive Synthesis Card ────────────────── */}
          {timelineData.executive_synthesis && (
            <div className="rounded-2xl border border-accent/30 bg-surface-2/90 p-5 space-y-4 shadow-md">
              <div className="flex items-center justify-between border-b border-border/60 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-accent-glow" />
                  <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
                    Cross-Company Incident Forensics & Market Reaction Synthesis
                  </h3>
                </div>
                <span className="text-2xs font-semibold px-2 py-0.5 rounded-full bg-tailwind-dim text-tailwind border border-tailwind/20">
                  Deep Research Verified
                </span>
              </div>

              {/* Core Themes Pills */}
              {timelineData.core_themes && timelineData.core_themes.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-2xs font-semibold text-text-muted mr-1">
                    Key Themes:
                  </span>
                  {timelineData.core_themes.map((theme, i) => (
                    <span
                      key={i}
                      className="text-2xs font-medium px-2.5 py-0.5 rounded-full bg-surface-3 border border-border text-text-secondary"
                    >
                      {theme}
                    </span>
                  ))}
                </div>
              )}

              {/* Markdown-style synthesis text */}
              <div className="text-xs text-text-secondary leading-relaxed space-y-3 pt-1">
                {timelineData.executive_synthesis
                  .split('\n\n')
                  .filter(Boolean)
                  .map((para, pIdx) => (
                    <p key={pIdx}>{para.replace(/\*\*/g, '')}</p>
                  ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column (4 cols): Interactive Milestone Forensics Inspector */}
        <div className="xl:col-span-4 sticky top-20 space-y-4">
          <div className="rounded-2xl border border-border/90 bg-surface-2/95 backdrop-blur-md p-5 shadow-2xl space-y-5">
            {/* Inspector Header */}
            <div className="flex items-center justify-between border-b border-border/70 pb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-accent-glow" />
                <span className="text-xs font-bold text-text-primary uppercase tracking-wider">
                  Milestone Forensics
                </span>
              </div>
              <span className="text-3xs uppercase font-mono font-bold px-2 py-0.5 rounded bg-accent/15 text-accent-glow border border-accent/30">
                INSPECTOR ACTIVE
              </span>
            </div>

            {selectedMilestone ? (
              <div className="space-y-4">
                {/* Milestone Title & Phase Box */}
                <div className="p-3.5 rounded-xl bg-surface-1 border border-border/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-accent-glow uppercase tracking-wide">
                      {selectedMilestone.company.company_name}
                    </span>
                    <span
                      className={cn(
                        'text-2xs px-2 py-0.5 rounded-full font-semibold border',
                        getPhaseColors(selectedMilestone.milestone.phase).badge,
                      )}
                    >
                      {selectedMilestone.milestone.phase}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-text-primary leading-snug">
                    {selectedMilestone.milestone.event}
                  </h4>
                  <div className="flex items-center gap-2 text-2xs text-text-muted pt-1 border-t border-border/50">
                    <Calendar className="w-3.5 h-3.5 text-text-muted" />
                    <span className="font-mono">{selectedMilestone.milestone.date}</span>
                  </div>
                </div>

                {/* Stock Price Card on Milestone Date */}
                <div className="p-4 rounded-xl bg-surface-3/80 border border-border space-y-3">
                  <div className="flex items-center justify-between border-b border-border/60 pb-2 text-2xs text-text-muted">
                    <span>Stock Price at Milestone Date</span>
                    <span className="font-mono font-semibold px-1.5 py-0.5 rounded bg-surface-1 text-text-secondary border border-border">
                      {selectedMilestone.company.stock_ticker || 'N/A'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <span className="text-3xs text-text-muted uppercase block">
                        Closing Price
                      </span>
                      <div className="text-lg font-mono font-bold text-tailwind">
                        {selectedMilestone.milestone.stock_price !== null &&
                        selectedMilestone.milestone.stock_price !== undefined
                          ? `$${selectedMilestone.milestone.stock_price.toFixed(2)}`
                          : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <span className="text-3xs text-text-muted uppercase block">
                        Change vs Baseline
                      </span>
                      <div
                        className={cn(
                          'text-lg font-mono font-bold',
                          selectedMilestone.milestone.stock_change_from_baseline_pct !== null &&
                            selectedMilestone.milestone.stock_change_from_baseline_pct !== undefined &&
                            selectedMilestone.milestone.stock_change_from_baseline_pct < 0
                            ? 'text-headwind'
                            : 'text-tailwind',
                        )}
                      >
                        {selectedMilestone.milestone.stock_change_from_baseline_pct !== null &&
                        selectedMilestone.milestone.stock_change_from_baseline_pct !== undefined
                          ? `${
                              selectedMilestone.milestone.stock_change_from_baseline_pct > 0
                                ? '+'
                                : ''
                            }${selectedMilestone.milestone.stock_change_from_baseline_pct.toFixed(
                              1,
                            )}%`
                          : 'N/A'}
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-border/60 flex items-center justify-between text-2xs text-text-muted font-mono">
                    <span>Trading Volume:</span>
                    <span className="text-text-primary font-semibold">
                      {selectedMilestone.milestone.trading_volume
                        ? selectedMilestone.milestone.trading_volume.toLocaleString()
                        : 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Measurable Impact & Consequences */}
                <div className="space-y-1.5">
                  <span className="text-2xs font-semibold text-headwind flex items-center gap-1.5 uppercase tracking-wide">
                    <ShieldAlert className="w-3.5 h-3.5 text-headwind" />
                    <span>Measurable Impact</span>
                  </span>
                  <div className="text-xs text-text-secondary leading-relaxed bg-headwind-dim/40 p-3 rounded-xl border border-headwind/20">
                    {selectedMilestone.milestone.impact}
                  </div>
                </div>

                {/* Mini Stock Sparkline Highlight */}
                {selectedMilestone.company.stock_metrics?.daily_series && (
                  <div className="space-y-1.5">
                    <span className="text-2xs font-semibold text-text-muted flex items-center gap-1.5 uppercase tracking-wide">
                      <LineChart className="w-3.5 h-3.5 text-accent-glow" />
                      <span>Stock Path & Milestone Marker (Red Dot)</span>
                    </span>
                    <div className="h-28 rounded-xl bg-surface-1/90 border border-border p-2">
                      <ReactECharts
                        option={buildMiniSparklineOption(
                          selectedMilestone.company,
                          selectedMilestone.milestone.date,
                        )}
                        style={{ height: '100%', width: '100%' }}
                        notMerge
                      />
                    </div>
                  </div>
                )}

                {/* Key Parallels & Differences */}
                {selectedMilestone.company.key_parallels?.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider block">
                      Key Parallels to Current Scenario:
                    </span>
                    <ul className="space-y-1 text-2xs text-text-secondary">
                      {selectedMilestone.company.key_parallels.slice(0, 3).map((p, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-tailwind mt-0.5">•</span>
                          <span>{p}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Sources & Citations */}
                {selectedMilestone.company.sources?.length > 0 && (
                  <div className="pt-2 border-t border-border/60 space-y-1.5">
                    <span className="text-2xs font-semibold text-text-muted uppercase tracking-wider block">
                      Verified Citations & Sources:
                    </span>
                    <div className="space-y-1">
                      {selectedMilestone.company.sources.slice(0, 2).map((s, idx) => (
                        <a
                          key={idx}
                          href={s.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center justify-between text-2xs text-accent-glow hover:underline truncate"
                        >
                          <span className="truncate">{s.title}</span>
                          <ExternalLink className="w-3 h-3 shrink-0 ml-1 opacity-70" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-16 text-center text-xs text-text-muted space-y-2">
                <Target className="w-6 h-6 mx-auto text-text-muted opacity-50" />
                <p>Click any milestone node to inspect its forensic stock data.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── New Deep Research Modal ──────────────────────────────────── */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-1 border border-border rounded-2xl w-full max-w-xl shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-border/70 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-accent/15 text-accent-glow">
                  <Sparkles className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-text-primary">
                  Run Deep Research on Corporate Incident
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="text-text-muted hover:text-text-primary transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <label className="block text-xs font-semibold text-text-secondary">
                Enter Scenario or News Description:
              </label>
              <textarea
                rows={3}
                value={researchPrompt}
                onChange={e => setResearchPrompt(e.target.value)}
                placeholder="e.g., A Fortune 500 board abruptly forces out the CEO amidst manufacturing delays and operating losses..."
                className="w-full bg-surface-2 border border-border rounded-xl p-3 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent"
              />

              <div className="flex items-center justify-between text-xs text-text-muted">
                <span>Number of Corporate Analogs to Discover:</span>
                <select
                  value={companyCount}
                  onChange={e => setCompanyCount(parseInt(e.target.value, 10))}
                  className="bg-surface-2 border border-border rounded-lg px-2.5 py-1 text-xs text-text-primary focus:outline-none"
                >
                  <option value={5}>5 Major Companies</option>
                  <option value={6}>6 Major Companies</option>
                  <option value={8}>8 Major Companies</option>
                  <option value={10}>10 Major Companies</option>
                </select>
              </div>

              {/* Sample Quick Scenarios */}
              <div className="space-y-1.5 pt-2">
                <span className="text-3xs uppercase tracking-wider font-semibold text-text-muted">
                  Or select a benchmark scenario:
                </span>
                <div className="grid grid-cols-1 gap-1.5 text-xs">
                  {QUICK_PROMPTS.map((p, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setResearchPrompt(p.prompt)}
                      className="text-left p-2 rounded-lg bg-surface-2 hover:bg-surface-3 border border-border/70 text-text-secondary hover:text-text-primary transition truncate"
                    >
                      {p.title}
                    </button>
                  ))}
                </div>
              </div>

              {researchError && (
                <div className="p-3 rounded-lg bg-headwind-dim border border-headwind/20 text-xs text-headwind">
                  {researchError}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-border/70">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-surface-2 hover:bg-surface-3 text-xs font-medium text-text-muted hover:text-text-primary transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleTriggerResearch}
                disabled={isResearching || !researchPrompt.trim()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent hover:bg-accent-glow text-white text-xs font-semibold shadow-md shadow-accent/20 transition disabled:opacity-50"
              >
                <span>Execute Deep Research</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Research Execution Loading Overlay ───────────────────────── */}
      {isResearching && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center p-4 space-y-4">
          <div className="relative w-16 h-16">
            <div className="w-16 h-16 rounded-full border-4 border-surface-3 border-t-accent animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Network className="w-6 h-6 text-accent-glow animate-pulse" />
            </div>
          </div>
          <div className="text-center space-y-1">
            <h3 className="text-base font-bold text-text-primary">
              Deep Research Agent Active...
            </h3>
            <p className="text-xs text-accent-glow font-mono max-w-sm">{loadingStep}</p>
            <p className="text-3xs text-text-muted">
              Querying neural search, identifying companies, fetching historical yfinance stock
              prices & milestones.
            </p>
          </div>
        </div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Helpers & ECharts Option Builders
// ---------------------------------------------------------------------------

function getPhaseColors(phase: string) {
  const p = phase.toLowerCase()
  if (p.includes('outbreak') || p.includes('crisis') || p.includes('crash') || p.includes('loss')) {
    return {
      badge: 'bg-headwind-dim text-headwind border-headwind/30',
      dot: 'bg-rose-500',
    }
  }
  if (p.includes('contain') || p.includes('resol') || p.includes('rollback')) {
    return {
      badge: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
      dot: 'bg-purple-400',
    }
  }
  if (p.includes('aftermath') || p.includes('review') || p.includes('legal') || p.includes('rebound')) {
    return {
      badge: 'bg-tailwind-dim text-tailwind border-tailwind/30',
      dot: 'bg-emerald-400',
    }
  }
  // Default Trigger / Precursor
  return {
    badge: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    dot: 'bg-amber-400',
  }
}

function buildCompanyStockChartOption(comp: CompanyIncidentReport) {
  const sm = comp.stock_metrics
  if (!sm || !sm.daily_series?.length) return {}

  const dates = sm.daily_series.map(d => d.date)
  const prices = sm.daily_series.map(d => d.close)
  const milestoneDates = new Set((comp.timeline || []).map(m => m.date.slice(0, 10)))

  return {
    backgroundColor: 'transparent',
    grid: { left: 40, right: 15, top: 12, bottom: 20 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      textStyle: { color: '#f1f5f9', fontSize: 11 },
      formatter: (params: any) => {
        if (!params || !params.length) return ''
        const date = params[0].axisValue
        const price = params[0].value
        const isMilestone = milestoneDates.has(date)
        return `<b>${date}</b><br/>Closing Price: <b>$${Number(price).toFixed(2)}</b>${
          isMilestone ? '<br/><span style="color:#f43f5e">● Incident Milestone</span>' : ''
        }`
      },
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { color: '#64748b', fontSize: 9 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: '#64748b',
        fontSize: 9,
        formatter: (v: number) => `$${v}`,
      },
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
    },
    series: [
      {
        name: comp.stock_ticker || comp.company_name,
        type: 'line',
        data: prices,
        smooth: true,
        lineStyle: { width: 2, color: '#38bdf8' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(56, 189, 248, 0.25)' },
              { offset: 1, color: 'rgba(56, 189, 248, 0.0)' },
            ],
          },
        },
        symbol: (val: any, params: any) => {
          const date = dates[params.dataIndex]
          return milestoneDates.has(date) ? 'circle' : 'none'
        },
        symbolSize: 8,
        itemStyle: {
          color: '#f43f5e',
          borderColor: '#ffffff',
          borderWidth: 1.5,
        },
      },
    ],
  }
}

function buildMiniSparklineOption(comp: CompanyIncidentReport, highlightDate: string) {
  const sm = comp.stock_metrics
  if (!sm || !sm.daily_series?.length) return {}

  const dates = sm.daily_series.map(d => d.date)
  const prices = sm.daily_series.map(d => d.close)
  const targetDateStr = highlightDate.slice(0, 10)

  return {
    backgroundColor: 'transparent',
    grid: { left: 30, right: 10, top: 8, bottom: 15 },
    xAxis: {
      type: 'category',
      data: dates,
      show: false,
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: '#64748b', fontSize: 8 },
      splitLine: { show: false },
    },
    series: [
      {
        type: 'line',
        data: prices,
        smooth: true,
        lineStyle: { width: 1.5, color: '#0ea5e9' },
        areaStyle: { color: 'rgba(14, 165, 233, 0.1)' },
        symbol: (val: any, params: any) => {
          return dates[params.dataIndex] === targetDateStr ? 'circle' : 'none'
        },
        symbolSize: 7,
        itemStyle: {
          color: '#f43f5e',
          borderColor: '#ffffff',
          borderWidth: 2,
        },
      },
    ],
  }
}

function buildHierarchicalTreeOption(data: DeepResearchTimelineOutput) {
  const treeData = {
    name: data.incident_category || 'Incident Root',
    itemStyle: { color: '#0284c7' },
    children: (data.similar_company_events || []).map(comp => ({
      name: `${comp.company_name}\n[${comp.stock_ticker || 'N/A'}] Peak: ${
        comp.stock_metrics?.max_drawdown_pct !== undefined
          ? `${comp.stock_metrics.max_drawdown_pct.toFixed(1)}%`
          : ''
      }`,
      itemStyle: { color: '#1e293b', borderColor: '#38bdf8' },
      customData: { type: 'company', company: comp },
      children: (comp.timeline || []).map(m => {
        const price =
          m.stock_price !== null && m.stock_price !== undefined
            ? `$${m.stock_price.toFixed(1)}`
            : ''
        const chg =
          m.stock_change_from_baseline_pct !== null &&
          m.stock_change_from_baseline_pct !== undefined
            ? `${m.stock_change_from_baseline_pct > 0 ? '+' : ''}${m.stock_change_from_baseline_pct.toFixed(1)}%`
            : ''

        let nodeColor = '#f59e0b'
        const p = m.phase.toLowerCase()
        if (p.includes('outbreak') || p.includes('crisis')) nodeColor = '#f43f5e'
        else if (p.includes('contain') || p.includes('resol')) nodeColor = '#10b981'

        return {
          name: `${m.phase}\n${m.date.slice(5)}\n${price} (${chg})`,
          itemStyle: { color: '#090d16', borderColor: nodeColor },
          customData: { type: 'milestone', milestone: m, company: comp },
        }
      }),
    })),
  }

  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', triggerOn: 'mousemove' },
    series: [
      {
        type: 'tree',
        data: [treeData],
        top: '4%',
        left: '12%',
        bottom: '4%',
        right: '20%',
        symbolSize: 9,
        orient: 'LR',
        initialTreeDepth: 3,
        label: {
          position: 'right',
          verticalAlign: 'middle',
          align: 'left',
          fontSize: 10,
          color: '#cbd5e1',
          fontFamily: 'monospace',
        },
        leaves: {
          label: {
            position: 'right',
            verticalAlign: 'middle',
            align: 'left',
          },
        },
        lineStyle: {
          color: '#334155',
          curveness: 0.5,
        },
        expandAndCollapse: false,
        animationDuration: 550,
      },
    ],
  }
}

function buildCohortComparisonOption(companies: CompanyIncidentReport[]) {
  const series = companies.map((c, i) => {
    const sm = c.stock_metrics
    const data =
      sm?.daily_series?.map((d, dIdx) => [dIdx, (d.close / sm.baseline_price) * 100]) || []

    const colors = ['#38bdf8', '#f43f5e', '#a855f7', '#34d399', '#fbbf24', '#ec4899']
    return {
      name: `${c.company_name} (${c.stock_ticker || 'N/A'})`,
      type: 'line',
      data,
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2, color: colors[i % colors.length] },
    }
  })

  return {
    backgroundColor: 'transparent',
    grid: { left: 45, right: 20, top: 30, bottom: 25 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      textStyle: { color: '#f1f5f9', fontSize: 11 },
      formatter: (params: any) => {
        if (!params || !params.length) return ''
        let html = `<b>Day ${params[0].value[0]}</b><br/>`
        params.forEach((item: any) => {
          const val = item.value[1]
          html += `<span style="color:${item.color}">●</span> ${item.seriesName}: <b>${val.toFixed(1)}</b> (${val >= 100 ? '+' : ''}${(val - 100).toFixed(1)}%)<br/>`
        })
        return html
      },
    },
    legend: {
      textStyle: { color: '#94a3b8', fontSize: 10 },
      top: 0,
      type: 'scroll',
    },
    xAxis: {
      type: 'value',
      name: 'Relative Trading Days',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'Indexed (Day 0 = 100)',
      nameTextStyle: { color: '#64748b', fontSize: 9 },
      axisLabel: { color: '#64748b', fontSize: 9 },
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
    },
    series,
  }
}
