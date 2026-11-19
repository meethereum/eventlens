import { useState, useEffect, useMemo, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  Sparkles,
  TrendingDown,
  Network,
  Columns,
  Calendar,
  AlertTriangle,
  X,
  RefreshCw,
  ArrowRight,
  Loader2,
  ExternalLink,
  LineChart,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type {
  DeepResearchTimelineOutput,
  CompanyIncidentReport,
  TimelineMilestone,
} from '@/types'
import { DEFAULT_TIMELINE_DATA } from '@/lib/defaultTimelineData'
import { companyName } from '@/lib/companies'

interface Props {
  ticker?: string
  eventType?: string
  asOf?: string
  marketMood?: string
  query?: string
}

type ViewMode = 'tracks' | 'tree'

const QUICK_PROMPTS = [
  { title: 'Executive ouster at a large manufacturer',
    prompt: 'A Fortune 500 board abruptly forces out the CEO amidst operational underperformance, manufacturing delays, or strategic misalignment' },
  { title: 'Digital bank run and liquidity crisis',
    prompt: 'A major commercial bank suffers an acute digital bank run due to unrealized bond losses and uninsured deposit flight' },
  { title: 'Antitrust lawsuit against a tech giant',
    prompt: 'A dominant technology corporation faces a major DOJ antitrust lawsuit or regulatory enforcement action' },
  { title: 'Manufacturing defect and safety grounding',
    prompt: 'A major manufacturer suffers a safety quality defect or regulatory grounding of its product line' },
  { title: 'Earnings cliff and restructuring',
    prompt: 'A market-leading company reports unexpected revenue collapse and slashes forward guidance, triggering restructuring' },
  { title: 'Major cybersecurity outage',
    prompt: 'A cybersecurity glitch takes down airlines, banks, and hospital IT systems worldwide' },
]

export default function PrecedentPanel({
  ticker = 'INTC',
  eventType = 'CEO departure',
  asOf = '',
  marketMood = 'mixed',
  query = '',
}: Props) {
  const effectivePrompt = useMemo(() => {
    const q = (query || '').trim()
    if (q) return q
    if (ticker && eventType && eventType !== 'Corporate Incident') {
      const co = ({ NVDA:'Nvidia',INTC:'Intel',AAPL:'Apple',MSFT:'Microsoft',
                     GM:'General Motors',SBUX:'Starbucks',AMZN:'Amazon',DIS:'Disney',
                     BA:'Boeing',RTX:'RTX',XOM:'ExxonMobil',CVX:'Chevron',
                     JPM:'JPMorgan Chase',SCHW:'Charles Schwab',UNH:'UnitedHealth',
                   } as Record<string,string>)[ticker.toUpperCase()] ?? ticker
      return `${co}: ${eventType}`
    }
    return DEFAULT_TIMELINE_DATA.query_prompt
  }, [query, ticker, eventType])

  const [timelineData, setTimelineData]       = useState<DeepResearchTimelineOutput>(DEFAULT_TIMELINE_DATA)
  const [selectedCompanyIdx, setSelectedCompanyIdx] = useState<string>('all')
  const [viewMode, setViewMode]               = useState<ViewMode>('tracks')
  const [isFetching, setIsFetching]           = useState(false)
  const [inspector, setInspector]             = useState<{ milestone: TimelineMilestone; company: CompanyIncidentReport } | null>(null)
  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set())

  // Research modal
  const [isModalOpen, setIsModalOpen]         = useState(false)
  const [researchPrompt, setResearchPrompt]   = useState(effectivePrompt)
  const [companyCount, setCompanyCount]       = useState(5)
  const [isResearching, setIsResearching]     = useState(false)
  const [loadingStep, setLoadingStep]         = useState('')
  const [researchError, setResearchError]     = useState<string | null>(null)

  useEffect(() => {
    if (effectivePrompt) setResearchPrompt(effectivePrompt)
  }, [effectivePrompt])

  const fetchTimeline = useCallback(async (prompt: string, t?: string, et?: string) => {
    setIsFetching(true)
    try {
      const p = new URLSearchParams()
      if (prompt) p.set('prompt', prompt)
      if (t) p.set('ticker', t)
      if (et) p.set('event_type', et)
      const res = await fetch(`/api/precedents/timeline?${p}`)
      if (!res.ok) throw new Error()
      const data = await res.json()
      if (data?.similar_company_events?.length > 0) {
        setTimelineData(data)
        setSelectedCompanyIdx('all')
        setExpandedCompanies(new Set())
      }
    } catch { /* use default */ }
    finally { setIsFetching(false) }
  }, [])

  useEffect(() => {
    fetchTimeline(effectivePrompt, ticker, eventType)
  }, [effectivePrompt, ticker, eventType, fetchTimeline])

  const handleResearch = async () => {
    if (!researchPrompt.trim()) return
    setIsResearching(true)
    setResearchError(null)
    const steps = [
      'Looking for similar past events...',
      'Checking company histories...',
      'Mapping stock prices...',
      'Pulling milestones...',
      'Finishing up...',
    ]
    let idx = 0
    const timer = setInterval(() => { idx = (idx + 1) % steps.length; setLoadingStep(steps[idx]) }, 3000)
    try {
      const res = await fetch('/api/precedents/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: researchPrompt.trim(), companies: companyCount }),
      })
      if (!res.ok) throw new Error(`Failed (${res.status})`)
      const data = await res.json()
      if (data?.similar_company_events) {
        setTimelineData(data)
        setSelectedCompanyIdx('all')
        setExpandedCompanies(new Set())
      }
      setIsModalOpen(false)
    } catch (e) {
      setResearchError((e as Error).message)
    } finally {
      clearInterval(timer)
      setIsResearching(false)
    }
  }

  const companies = timelineData.similar_company_events || []
  const filtered = selectedCompanyIdx === 'all'
    ? companies
    : companies.filter((_, i) => i.toString() === selectedCompanyIdx)

  const toggleExpand = (key: string) =>
    setExpandedCompanies(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  return (
    <section className="glass-panel p-5 space-y-5 relative">

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div>
          <h2 className="text-base font-semibold text-text-primary">Similar past events</h2>
          <p className="text-xs text-text-muted mt-0.5">
            What happened at other companies when something similar occurred
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="inline-flex rounded-lg border border-border bg-surface-3 p-0.5 text-xs">
            <button type="button" onClick={() => setViewMode('tracks')}
              className={cn('inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors',
                viewMode === 'tracks' ? 'bg-accent/20 text-accent-glow' : 'text-text-muted hover:text-text-secondary')}>
              <Columns className="w-3.5 h-3.5" /><span>Timeline</span>
            </button>
            <button type="button" onClick={() => setViewMode('tree')}
              className={cn('inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors',
                viewMode === 'tree' ? 'bg-accent/20 text-accent-glow' : 'text-text-muted hover:text-text-secondary')}>
              <Network className="w-3.5 h-3.5" /><span>Tree</span>
            </button>
          </div>

          <button type="button" onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-glow text-white text-xs font-medium transition-all">
            <Sparkles className="w-3.5 h-3.5" /><span>Find more</span>
          </button>

          <button type="button" onClick={() => fetchTimeline(effectivePrompt, ticker, eventType)} disabled={isFetching}
            className="p-1.5 rounded-lg border border-border bg-surface-2 hover:bg-surface-3 text-text-muted hover:text-text-primary transition disabled:opacity-50">
            <RefreshCw className={cn('w-4 h-4', isFetching && 'animate-spin text-accent-glow')} />
          </button>
        </div>
      </div>

      {/* Scenario context */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-2 border border-border/60 text-xs">
        <span className="text-text-muted shrink-0">Matching:</span>
        {isFetching ? (
          <span className="flex items-center gap-1.5 text-accent-glow">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Searching...
          </span>
        ) : (
          <span className="text-text-secondary truncate italic">"{timelineData.query_prompt}"</span>
        )}
        <span className="ml-auto text-text-muted shrink-0 font-mono">{companies.length} companies</span>
      </div>

      {/* Company filter */}
      <div className="flex flex-wrap gap-1.5">
        <button type="button" onClick={() => setSelectedCompanyIdx('all')}
          className={cn('px-2.5 py-1 rounded-full text-xs border transition-all',
            selectedCompanyIdx === 'all'
              ? 'bg-accent/20 text-accent-glow border-accent/40'
              : 'bg-surface-2 text-text-muted border-border hover:text-text-secondary')}>
          All
        </button>
        {companies.map((c, i) => (
          <button key={c.company_name + i} type="button" onClick={() => setSelectedCompanyIdx(i.toString())}
            className={cn('px-2.5 py-1 rounded-full text-xs border transition-all',
              selectedCompanyIdx === i.toString()
                ? 'bg-accent/20 text-accent-glow border-accent/40'
                : 'bg-surface-2 text-text-muted border-border hover:text-text-secondary')}>
            {c.company_name}
          </button>
        ))}
      </div>

      {/* ── TRACKS VIEW ─────────────────────────────────────────────── */}
      {viewMode === 'tracks' && (
        <div className="space-y-3">
          {filtered.map((comp, ci) => {
            const sm = comp.stock_metrics
            const dd = sm?.max_drawdown_pct
            const key = comp.company_name + ci
            const isExpanded = expandedCompanies.has(key)
            const milestones = comp.timeline || []

            return (
              <div key={key} className="rounded-xl border border-border/70 bg-surface-2/60 overflow-hidden">
                {/* Company row — always visible */}
                <button type="button" onClick={() => toggleExpand(key)}
                  className="w-full flex items-center justify-between gap-3 px-4 py-3 hover:bg-surface-3/50 transition-colors text-left">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-text-primary truncate">
                          {comp.company_name}
                        </span>
                        {dd !== undefined && (
                          <span className="text-xs font-mono font-medium text-headwind shrink-0">
                            −{Math.abs(dd).toFixed(1)}%
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-text-muted truncate">{comp.incident_title} · {comp.event_timeframe}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {sm && (
                      <div className="hidden sm:flex items-center gap-4 text-xs font-mono text-text-muted">
                        <span>${sm.baseline_price.toFixed(0)} → <span className="text-headwind">${sm.trough_price.toFixed(0)}</span></span>
                      </div>
                    )}
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-text-muted" /> : <ChevronDown className="w-4 h-4 text-text-muted" />}
                  </div>
                </button>

                {/* Expanded: milestones + chart */}
                {isExpanded && (
                  <div className="border-t border-border/50 px-4 pb-4 pt-3 space-y-4">
                    {/* Milestone tiles */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                      {milestones.map((m, mi) => {
                        const isSelected = inspector?.milestone === m && inspector?.company === comp
                        const pc = getPhaseColors(m.phase)
                        const chg = m.stock_change_from_baseline_pct
                        return (
                          <button key={m.date + mi} type="button"
                            onClick={() => setInspector({ milestone: m, company: comp })}
                            className={cn(
                              'text-left p-3 rounded-lg border space-y-1.5 transition-all',
                              isSelected
                                ? 'border-accent bg-accent/10 ring-1 ring-accent/30'
                                : 'border-border bg-surface-3/50 hover:border-accent/40',
                            )}>
                            <div className="flex items-center justify-between gap-1">
                              <span className={cn('text-2xs font-medium px-1.5 py-0.5 rounded-full border', pc.badge)}>
                                {m.phase}
                              </span>
                              {chg !== null && chg !== undefined && (
                                <span className={cn('text-2xs font-mono font-bold', chg < 0 ? 'text-headwind' : 'text-tailwind')}>
                                  {chg > 0 ? '+' : ''}{chg.toFixed(1)}%
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">{m.event}</p>
                            <div className="text-2xs text-text-muted font-mono">{m.date.slice(0, 10)}</div>
                          </button>
                        )
                      })}
                    </div>

                    {/* Stock chart */}
                    {sm?.daily_series && sm.daily_series.length > 0 && (
                      <div className="h-28 rounded-lg bg-surface-1/80 border border-border/50 p-2">
                        <ReactECharts option={buildStockChart(comp)} style={{ height: '100%', width: '100%' }} notMerge />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* ── TREE VIEW ───────────────────────────────────────────────── */}
      {viewMode === 'tree' && (
        <div className="rounded-xl border border-border/70 bg-surface-2/60 p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border/50 pb-2">
            <div className="flex items-center gap-2">
              <Network className="w-4 h-4 text-accent-glow" />
              <span className="text-xs font-medium text-text-primary">
                Drag nodes to rearrange · Scroll to zoom · Click a milestone node to inspect it
              </span>
            </div>
            <div className="flex items-center gap-3 text-2xs text-text-muted">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-accent/60 inline-block" /> Company</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-amber-400 inline-block" /> Trigger</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-rose-500 inline-block" /> Crisis</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-purple-400 inline-block" /> Containment</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-emerald-400 inline-block" /> Aftermath</span>
            </div>
          </div>
          <div className="rounded-lg bg-surface-1/80 border border-border/50 overflow-hidden" style={{ height: '420px' }}>
            <ReactECharts
              option={buildGraphOption(filtered, timelineData.incident_category)}
              style={{ height: '100%', width: '100%' }}
              onEvents={{
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                click: (params: any) => {
                  const d = params?.data?.customData
                  if (d?.type === 'milestone') setInspector({ milestone: d.milestone, company: d.company })
                },
              }}
              notMerge
            />
          </div>
        </div>
      )}

      {/* Executive synthesis */}
      {timelineData.executive_synthesis && (
        <div className="rounded-xl border border-border/50 bg-surface-2/50 p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-medium text-text-secondary">
            <Sparkles className="w-3.5 h-3.5 text-accent-glow" />
            What these precedents have in common
          </div>
          <p className="text-sm text-text-secondary leading-relaxed">
            {timelineData.executive_synthesis.replace(/\*\*/g, '').split('\n\n')[0]}
          </p>
        </div>
      )}

      {/* ── INSPECTOR SLIDE-IN ───────────────────────────────────────── */}
      {inspector && (
        <>
          <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={() => setInspector(null)} />
          <div className="fixed inset-y-0 right-0 z-50 w-full max-w-sm flex flex-col bg-surface-1 border-l border-border shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
              <div className="min-w-0">
                <div className="text-xs font-medium text-text-muted">{inspector.company.company_name}</div>
                <div className={cn('inline-flex items-center gap-1 mt-1 text-2xs font-medium px-2 py-0.5 rounded-full border',
                  getPhaseColors(inspector.milestone.phase).badge)}>
                  {inspector.milestone.phase}
                </div>
              </div>
              <button onClick={() => setInspector(null)}
                className="p-1.5 rounded-lg hover:bg-surface-3 text-text-muted hover:text-text-primary transition">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {/* Event */}
              <div>
                <p className="text-sm font-medium text-text-primary leading-snug">{inspector.milestone.event}</p>
                <div className="flex items-center gap-1.5 mt-2 text-xs text-text-muted">
                  <Calendar className="w-3.5 h-3.5" />
                  <span className="font-mono">{inspector.milestone.date.slice(0, 10)}</span>
                </div>
              </div>

              {/* Stock price */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-3/60 rounded-lg p-3">
                  <div className="text-2xs text-text-muted mb-1">Stock price that day</div>
                  <div className="text-lg font-mono font-bold text-text-primary">
                    {inspector.milestone.stock_price != null
                      ? `$${inspector.milestone.stock_price.toFixed(2)}`
                      : '—'}
                  </div>
                </div>
                <div className="bg-surface-3/60 rounded-lg p-3">
                  <div className="text-2xs text-text-muted mb-1">Change from before event</div>
                  <div className={cn('text-lg font-mono font-bold',
                    (inspector.milestone.stock_change_from_baseline_pct ?? 0) < 0 ? 'text-headwind' : 'text-tailwind')}>
                    {inspector.milestone.stock_change_from_baseline_pct != null
                      ? `${inspector.milestone.stock_change_from_baseline_pct > 0 ? '+' : ''}${inspector.milestone.stock_change_from_baseline_pct.toFixed(1)}%`
                      : '—'}
                  </div>
                </div>
              </div>

              {/* Impact */}
              <div className="bg-headwind-dim/40 border border-headwind/20 rounded-lg p-3">
                <div className="flex items-center gap-1.5 text-xs font-medium text-headwind mb-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> What happened
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">{inspector.milestone.impact}</p>
              </div>

              {/* Mini sparkline */}
              {inspector.company.stock_metrics?.daily_series && (
                <div className="space-y-1.5">
                  <div className="text-2xs text-text-muted flex items-center gap-1">
                    <LineChart className="w-3.5 h-3.5" /> Stock path — red dot = this event
                  </div>
                  <div className="h-24 rounded-lg bg-surface-1/80 border border-border/50 p-2">
                    <ReactECharts
                      option={buildSparkline(inspector.company, inspector.milestone.date)}
                      style={{ height: '100%', width: '100%' }} notMerge />
                  </div>
                </div>
              )}

              {/* Parallels */}
              {inspector.company.key_parallels?.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-xs font-medium text-text-secondary">Why this case is similar</div>
                  <ul className="space-y-1">
                    {inspector.company.key_parallels.slice(0, 3).map((p, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-text-muted">
                        <span className="text-tailwind mt-0.5 shrink-0">•</span> {p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Sources */}
              {inspector.company.sources?.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-border/50">
                  <div className="text-2xs text-text-muted font-medium">Sources</div>
                  {inspector.company.sources.slice(0, 2).map((s, i) => (
                    <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center justify-between text-2xs text-accent-glow hover:underline truncate">
                      <span className="truncate">{s.title}</span>
                      <ExternalLink className="w-3 h-3 ml-1 shrink-0 opacity-70" />
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* ── RESEARCH MODAL ──────────────────────────────────────────── */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-1 border border-border rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <h3 className="text-sm font-semibold text-text-primary">Find similar past events</h3>
              <button type="button" onClick={() => setIsModalOpen(false)}
                className="text-text-muted hover:text-text-primary transition">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <label className="block text-xs text-text-secondary">Describe the scenario:</label>
              <textarea rows={3} value={researchPrompt} onChange={e => setResearchPrompt(e.target.value)}
                placeholder="e.g., A major company abruptly replaces its CEO after a period of poor results..."
                className="w-full bg-surface-2 border border-border rounded-xl p-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent" />

              <div className="flex items-center justify-between text-xs text-text-muted">
                <span>Number of companies to find:</span>
                <select value={companyCount} onChange={e => setCompanyCount(parseInt(e.target.value, 10))}
                  className="bg-surface-2 border border-border rounded-lg px-2.5 py-1 text-xs text-text-primary focus:outline-none">
                  {[3, 5, 8, 10].map(n => <option key={n} value={n}>{n} companies</option>)}
                </select>
              </div>

              <div className="space-y-1.5">
                <div className="text-2xs text-text-muted">Or pick an example:</div>
                {QUICK_PROMPTS.map((p, i) => (
                  <button key={i} type="button" onClick={() => setResearchPrompt(p.prompt)}
                    className="w-full text-left p-2.5 rounded-lg bg-surface-2 hover:bg-surface-3 border border-border/60 text-xs text-text-secondary hover:text-text-primary transition">
                    {p.title}
                  </button>
                ))}
              </div>

              {researchError && (
                <div className="p-3 rounded-lg bg-headwind-dim border border-headwind/20 text-xs text-headwind">
                  {researchError}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-border/60">
              <button type="button" onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-surface-2 hover:bg-surface-3 text-xs text-text-muted hover:text-text-primary transition">
                Cancel
              </button>
              <button type="button" onClick={handleResearch} disabled={isResearching || !researchPrompt.trim()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent hover:bg-accent-glow text-white text-xs font-medium transition disabled:opacity-50">
                Search <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Research loading overlay */}
      {isResearching && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center gap-4">
          <div className="w-12 h-12 rounded-full border-4 border-surface-3 border-t-accent animate-spin" />
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-text-primary">Searching past events...</p>
            <p className="text-xs text-accent-glow font-mono">{loadingStep}</p>
          </div>
        </div>
      )}
    </section>
  )
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function getPhaseColors(phase: string) {
  const p = phase.toLowerCase()
  if (p.includes('outbreak') || p.includes('crisis') || p.includes('crash'))
    return { badge: 'bg-headwind-dim text-headwind border-headwind/30', dot: 'bg-rose-500' }
  if (p.includes('contain') || p.includes('resol'))
    return { badge: 'bg-purple-500/15 text-purple-300 border-purple-500/30', dot: 'bg-purple-400' }
  if (p.includes('aftermath') || p.includes('rebound'))
    return { badge: 'bg-tailwind-dim text-tailwind border-tailwind/30', dot: 'bg-emerald-400' }
  return { badge: 'bg-amber-500/15 text-amber-300 border-amber-500/30', dot: 'bg-amber-400' }
}

function buildStockChart(comp: CompanyIncidentReport) {
  const sm = comp.stock_metrics
  if (!sm?.daily_series?.length) return {}
  const dates = sm.daily_series.map(d => d.date)
  const prices = sm.daily_series.map(d => d.close)
  const mDates = new Set((comp.timeline || []).map(m => m.date.slice(0, 10)))
  return {
    backgroundColor: 'transparent',
    grid: { left: 36, right: 10, top: 8, bottom: 18 },
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#64748b', fontSize: 9 }, axisLine: { lineStyle: { color: '#334155' } } },
    yAxis: { type: 'value', scale: true, axisLabel: { color: '#64748b', fontSize: 9, formatter: (v: number) => `$${v}` }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } } },
    series: [{
      type: 'line', data: prices, smooth: true,
      lineStyle: { width: 1.5, color: '#38bdf8' },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(56,189,248,0.2)' }, { offset: 1, color: 'rgba(56,189,248,0)' }] } },
      symbol: (_v: any, p: any) => mDates.has(dates[p.dataIndex]) ? 'circle' : 'none',
      symbolSize: 6,
      itemStyle: { color: '#f43f5e', borderColor: '#fff', borderWidth: 1.5 },
    }],
  }
}

function buildSparkline(comp: CompanyIncidentReport, highlightDate: string) {
  const sm = comp.stock_metrics
  if (!sm?.daily_series?.length) return {}
  const dates = sm.daily_series.map(d => d.date)
  const prices = sm.daily_series.map(d => d.close)
  const target = highlightDate.slice(0, 10)
  return {
    backgroundColor: 'transparent',
    grid: { left: 28, right: 8, top: 6, bottom: 14 },
    xAxis: { type: 'category', data: dates, show: false },
    yAxis: { type: 'value', scale: true, axisLabel: { color: '#64748b', fontSize: 8 }, splitLine: { show: false } },
    series: [{
      type: 'line', data: prices, smooth: true,
      lineStyle: { width: 1.5, color: '#0ea5e9' },
      areaStyle: { color: 'rgba(14,165,233,0.1)' },
      symbol: (_v: any, p: any) => dates[p.dataIndex] === target ? 'circle' : 'none',
      symbolSize: 7,
      itemStyle: { color: '#f43f5e', borderColor: '#fff', borderWidth: 2 },
    }],
  }
}




function buildGraphOption(companies: CompanyIncidentReport[], rootLabel?: string) {
  function phaseColor(phase: string): string {
    const p = phase.toLowerCase()
    if (p.includes('outbreak') || p.includes('crisis') || p.includes('crash')) return '#f43f5e'
    if (p.includes('contain') || p.includes('resol')) return '#a855f7'
    if (p.includes('aftermath') || p.includes('rebound')) return '#10b981'
    return '#f59e0b'
  }

  const nodes: object[] = []
  const edges: object[] = []

  // Root node — centred, fixed
  const rootId = 'root'
  const shortRoot = rootLabel
    ? (rootLabel.length > 28 ? rootLabel.slice(0, 26) + '…' : rootLabel).split(':')[0].trim()
    : 'Event'

  nodes.push({
    id: rootId,
    name: shortRoot,
    x: 0, y: 0,
    fixed: true,
    symbolSize: 36,
    symbol: 'roundRect',
    itemStyle: { color: '#1d4ed8', borderColor: '#60a5fa', borderWidth: 2 },
    label: { show: true, fontSize: 11, fontWeight: 700, color: '#f1f5f9', position: 'inside' },
    customData: { type: 'root' },
  })

  // Place companies in a ring around the root
  const angleStep = (2 * Math.PI) / Math.max(companies.length, 1)
  const compRadius = 220

  companies.forEach((comp, ci) => {
    const compId = `comp-${ci}`
    const angle = ci * angleStep - Math.PI / 2
    const cx = Math.cos(angle) * compRadius
    const cy = Math.sin(angle) * compRadius
    const dd = comp.stock_metrics?.max_drawdown_pct
    const shortName = comp.company_name.length > 16
      ? comp.company_name.slice(0, 15) + '…'
      : comp.company_name
    const compLabel = dd !== undefined
      ? `${shortName}\n−${Math.abs(dd).toFixed(1)}%`
      : shortName

    nodes.push({
      id: compId,
      name: compLabel,
      x: cx, y: cy,
      symbolSize: 28,
      symbol: 'roundRect',
      itemStyle: { color: '#0f2744', borderColor: '#38bdf8', borderWidth: 2 },
      label: {
        show: true,
        fontSize: 10,
        fontWeight: 600,
        color: '#e2e8f0',
        position: 'outside',
        // Push label away from centre
        offset: [Math.cos(angle) * 10, Math.sin(angle) * 10],
      },
      customData: { type: 'company', company: comp },
    })

    edges.push({
      source: rootId,
      target: compId,
      lineStyle: { color: '#334155', width: 1.5, curveness: 0 },
    })

    // Place milestones in a smaller arc around each company
    const milestones = comp.timeline || []
    const mAngleSpread = Math.PI * 0.7
    const mRadius = 110

    milestones.forEach((m, mi) => {
      const nodeId = `${compId}-m${mi}`
      const mAngle = milestones.length === 1
        ? angle
        : angle + (mi / (milestones.length - 1) - 0.5) * mAngleSpread
      const mx = cx + Math.cos(mAngle) * mRadius
      const my = cy + Math.sin(mAngle) * mRadius
      const chg = m.stock_change_from_baseline_pct
      const color = phaseColor(m.phase)
      const shortPhase = m.phase.split('/')[0].split(' ')[0]  // first word only
      const chgStr = chg !== null && chg !== undefined
        ? ` ${chg > 0 ? '+' : ''}${chg.toFixed(1)}%`
        : ''

      nodes.push({
        id: nodeId,
        name: `${shortPhase}${chgStr}`,
        x: mx, y: my,
        symbolSize: 16,
        symbol: 'circle',
        itemStyle: { color: '#0f172a', borderColor: color, borderWidth: 2 },
        label: { show: true, fontSize: 9, color: '#cbd5e1', position: 'right', distance: 6 },
        customData: { type: 'milestone', milestone: m, company: comp },
      })

      // Chain milestones sequentially: company → m0 → m1 → m2…
      const source = mi === 0 ? compId : `${compId}-m${mi - 1}`
      edges.push({
        source,
        target: nodeId,
        lineStyle: { color: color + '90', width: 1.2, curveness: 0.15 },
      })
    })
  })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#141820',
      borderColor: '#1f2937',
      extraCssText: 'max-width:280px; white-space:normal; word-break:break-word;',
      textStyle: { color: '#f1f5f9', fontSize: 11, lineHeight: 18 },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      formatter: (params: any) => {
        const d = params?.data
        if (!d?.customData) return ''
        if (d.customData.type === 'milestone') {
          const m = d.customData.milestone as TimelineMilestone
          const chg = m.stock_change_from_baseline_pct
          const chgHtml = chg !== null && chg !== undefined
            ? `<span style="color:${chg < 0 ? '#f87171' : '#34d399'};font-weight:600">${chg > 0 ? '+' : ''}${chg.toFixed(1)}%</span>`
            : ''
          return `<b>${m.phase}</b> · <span style="color:#94a3b8">${m.date.slice(0, 10)}</span><br/>${m.event.length > 100 ? m.event.slice(0, 100) + '…' : m.event}${chgHtml ? '<br/>Stock move: ' + chgHtml : ''}`
        }
        if (d.customData.type === 'company') {
          const c = d.customData.company as CompanyIncidentReport
          const dd = c.stock_metrics?.max_drawdown_pct
          return `<b>${c.company_name}</b><br/>${c.incident_title}${dd !== undefined ? `<br/><span style="color:#f87171">Peak drop: −${Math.abs(dd).toFixed(1)}%</span>` : ''}`
        }
        return `<b>${(d.name as string).split('\n')[0]}</b>`
      },
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      edges,
      roam: true,
      draggable: true,
      focusNodeAdjacency: true,
      force: {
        repulsion: 300,
        gravity: 0.04,
        edgeLength: [70, 130],
        layoutAnimation: true,
        friction: 0.6,
      },
      lineStyle: { opacity: 0.7 },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 2.5, opacity: 1 },
        label: { show: true, fontSize: 11, fontWeight: 700 },
      },
      cursor: 'pointer',
    }],
  }
}
