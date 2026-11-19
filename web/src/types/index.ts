// -----------------------------------------------------------------------
// EventLens shared frontend types — mirrors backend Pydantic models
// -----------------------------------------------------------------------

export type CardStatus = 'queued' | 'fetching' | 'done' | 'error'
export type SignalLabel = 'tailwind' | 'neutral' | 'headwind'

export interface Headline {
  label: string
  value: number | string
  unit: string
  delta?: number | null
}

export interface Metric {
  name: string
  value: number | string | null
  unit: string
  note?: string
}

export interface Series {
  t: string   // ISO date
  v: number | null
}

export interface MathDetail {
  formula: string
  inputs: Record<string, unknown>
  contribution?: number | null
}

export interface Source {
  name: string
  url: string
  retrieved_at: string
}

export interface CardOutput {
  id: string
  title: string
  status: CardStatus
  as_of: string
  fetched_at: string
  latency_ms: number

  headline: Headline | null
  metrics: Metric[]
  series: Series[]

  signal: number          // [-1, 1]
  label: SignalLabel
  weight: number          // [0, 1]
  quality: number         // [0, 1]

  reasoning: string[]
  math: MathDetail | null
  sources: Source[]
  warnings: string[]

  error_message?: string | null
}

export interface ParsedQuery {
  ticker: string
  event_type: string
  as_of: string
  horizon_days: number
  intent: string
}

export interface ScenarioScore {
  name: string
  score: number
  ci_low: number
  ci_high: number
  rationale: string
  watch_for: string
}

export interface AggregateResult {
  composite_signal: number
  evidence_strength: number
  coverage: number
  scenarios: ScenarioScore[]
  card_contributions: Record<string, number>
}

export interface VerdictOutput {
  headline: string
  summary: string
  key_drivers: Array<{ card: string; point: string }>
  counter_evidence: Array<{ card: string; point: string }>
  scenarios: Array<{
    name: string
    score: number
    rationale: string
    watch_for: string
  }>
  confidence_statement: string
  data_gaps: string[]
  disclaimer: string
  references: Source[]
  is_fallback: boolean
  model_used: string
  is_fallback_model: boolean
}

// SSE event types
export interface SSEEvent {
  type:
    | 'query_parsed'
    | 'scope_check'
    | 'card_start'
    | 'card_done'
    | 'card_error'
    | 'aggregate'
    | 'verdict_delta'
    | 'verdict_done'
    | 'done'
    | 'error'
  data: unknown
}

// Analysis run state (held in React state)
export interface AnalysisState {
  runId: string | null
  query: string
  parsed: ParsedQuery | null
  cards: Record<string, CardOutput>
  aggregate: AggregateResult | null
  verdict: VerdictOutput | null
  verdictStream: string
  phase:
    | 'idle'
    | 'parsing'
    | 'scope_check'
    | 'fetching'
    | 'scoring'
    | 'synthesising'
    | 'done'
    | 'error'
  pipelineTimings: Record<string, number>  // phase -> ms
  error: string | null
}

// Health
export interface DataSourceHealth {
  name: string
  status: 'live' | 'cached' | 'demo' | 'error'
  last_updated?: string | null
  note?: string
}

export interface HealthResponse {
  status: string
  demo_mode: boolean
  missing_keys: string[]
  llm_base_url_host: string
  llm_model: string
  llm_model_available?: boolean | null
  data_sources: DataSourceHealth[]
  version: string
}

// -----------------------------------------------------------------------
// Deep Research Timeline & Precedent Schemas (from newagent)
// -----------------------------------------------------------------------

export interface TimelineMilestone {
  date: string
  phase: string
  event: string
  impact: string
  stock_price?: number | null
  stock_change_from_baseline_pct?: number | null
  trading_volume?: number | null
}

export interface DailyPricePoint {
  date: string
  close: number
}

export interface StockPerformanceMetrics {
  ticker: string
  baseline_date: string
  baseline_price: number
  trough_date: string
  trough_price: number
  max_drawdown_pct: number
  daily_series: DailyPricePoint[]
}

export interface SourceCitation {
  title: string
  url: string
}

export interface CompanyIncidentReport {
  company_name: string
  stock_ticker?: string | null
  industry: string
  incident_title: string
  event_timeframe: string
  summary: string
  similarity_rationale: string
  key_parallels: string[]
  key_differences: string[]
  timeline: TimelineMilestone[]
  stock_metrics?: StockPerformanceMetrics | null
  total_impact_assessment: string
  sources: SourceCitation[]
}

export interface DeepResearchTimelineOutput {
  query_prompt: string
  generated_at: string
  incident_category: string
  core_themes: string[]
  executive_synthesis: string
  total_companies_analyzed: number
  similar_company_events: CompanyIncidentReport[]
}
