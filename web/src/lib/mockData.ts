// -----------------------------------------------------------------------
// Mock data for M0 — drives the full UI without any backend calls.
// All 10 cards are populated with plausible INTC/2024-12-02 data.
// -----------------------------------------------------------------------
import type {
  CardOutput,
  AggregateResult,
  VerdictOutput,
  HealthResponse,
  ParsedQuery,
} from '@/types'

export const MOCK_QUERY = "Intel's CEO was just ousted. What should I expect?"

export const MOCK_PARSED: ParsedQuery = {
  ticker: 'INTC',
  event_type: 'CEO departure',
  as_of: '2024-12-02',
  horizon_days: 20,
  intent: 'analysis',
}

export const MOCK_HEALTH: HealthResponse = {
  status: 'demo',
  demo_mode: true,
  missing_keys: ['FRED_API_KEY', 'LLM_API_KEY'],
  llm_base_url_host: 'api.groq.com',
  llm_model: 'openai/gpt-oss-120b',
  llm_model_available: null,
  data_sources: [
    { name: 'FRED', status: 'demo', note: 'key not set' },
    { name: 'yfinance', status: 'demo', note: 'fixture replay' },
    { name: 'SEC EDGAR', status: 'demo', note: 'fixture replay' },
    { name: 'GPR', status: 'demo', note: 'bundled copy' },
    { name: 'LLM', status: 'demo', note: 'key not set' },
  ],
  version: '0.1.0',
}

const makeSeries = (n = 60, base = 100, vol = 0.015) =>
  Array.from({ length: n }, (_, i) => {
    const d = new Date('2024-10-01')
    d.setDate(d.getDate() + i)
    base = base * (1 + (Math.random() - 0.5) * vol)
    return { t: d.toISOString().slice(0, 10), v: +base.toFixed(3) }
  })

export const MOCK_CARDS: CardOutput[] = [
  {
    id: 'C1',
    title: 'USD Strength',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:03Z',
    latency_ms: 312,
    headline: { label: 'DXY Index', value: 106.2, unit: '', delta: 1.8 },
    metrics: [
      { name: 'Level', value: 106.2, unit: '' },
      { name: '20d change', value: 1.8, unit: '%' },
      { name: '60d change', value: 3.4, unit: '%' },
      { name: '1y percentile', value: 72, unit: '%ile' },
    ],
    series: makeSeries(60, 103),
    signal: -0.38,
    label: 'headwind',
    weight: 0.6,
    quality: 0.91,
    reasoning: [
      'DXY has risen 1.8% over the past 20 trading days, sitting at the 72nd percentile of its 1-year range.',
      'A strong dollar compresses overseas revenue when translated back to USD — Intel derives ~70% of sales internationally.',
      "Given the CEO change, investor uncertainty about Intel's strategic direction amplifies this currency headwind.",
      'The 60-day trend (+3.4%) suggests persistent USD strength rather than a transitory spike.',
    ],
    plain_title: 'United States dollar strength',
    plain_summary: 'The United States dollar changed 1.8% over the past 20 trading days and 3.4% over the past 60 trading days.',
    direction: 'against',
    strength: 'moderate',
    math: {
      formula: 's = d × tanh(z / 2)',
      inputs: { z: -1.2, rho: -0.31, d: -1 },
      contribution: -0.09,
    },
    sources: [
      { name: 'FRED DTWEXBGS', url: 'https://fred.stlouisfed.org/series/DTWEXBGS', retrieved_at: '2024-12-02T14:01:00Z' },
    ],
    warnings: [],
  },
  {
    id: 'C2',
    title: 'Rates & Inflation',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:05Z',
    latency_ms: 418,
    headline: { label: '10y Treasury', value: 4.21, unit: '%', delta: -0.12 },
    metrics: [
      { name: '10y yield', value: 4.21, unit: '%' },
      { name: '20d change', value: -12, unit: 'bp' },
      { name: 'Yield curve (10y–2y)', value: 0.08, unit: '%' },
      { name: 'CPI YoY', value: 2.6, unit: '%' },
    ],
    series: makeSeries(60, 4.4, 0.01),
    signal: -0.42,
    label: 'headwind',
    weight: 0.72,
    quality: 0.95,
    reasoning: [
      '10-year yields at 4.21% remain historically elevated despite a 12bp decline over the past month.',
      'High discount rates compress the present value of future earnings — particularly damaging for a capital-intensive fab business.',
      'Intel is in an expensive multi-year capex cycle (Intel Foundry Services); higher-for-longer rates increase the hurdle rate on these investments.',
      'CPI at 2.6% YoY shows inflation cooling but above the Fed target, suggesting rates stay elevated through 2025.',
    ],
    plain_title: 'Interest rates and inflation',
    plain_summary: 'The long term United States government borrowing rate is 4.21%, after changing by 12 basis points over 20 trading days. Prices rose 2.6% compared with a year ago.',
    direction: 'against',
    strength: 'moderate',
    math: {
      formula: 's = d × tanh(z / 2)',
      inputs: { z: -1.4, rho: -0.52, d: -1 },
      contribution: -0.14,
    },
    sources: [
      { name: 'FRED DGS10', url: 'https://fred.stlouisfed.org/series/DGS10', retrieved_at: '2024-12-02T14:01:04Z' },
      { name: 'FRED CPIAUCSL', url: 'https://fred.stlouisfed.org/series/CPIAUCSL', retrieved_at: '2024-12-02T14:01:04Z' },
    ],
    warnings: [],
  },
  {
    id: 'C3',
    title: 'Oil & Energy',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:07Z',
    latency_ms: 287,
    headline: { label: 'WTI Crude', value: 68.4, unit: '$/bbl', delta: -4.2 },
    metrics: [
      { name: 'WTI price', value: 68.4, unit: '$/bbl' },
      { name: '20d change', value: -4.2, unit: '%' },
      { name: '60d change', value: -9.1, unit: '%' },
      { name: '1y percentile', value: 28, unit: '%ile' },
    ],
    series: makeSeries(60, 73, 0.02),
    signal: 0.15,
    label: 'neutral',
    weight: 0.3,
    quality: 0.93,
    reasoning: [
      'WTI crude is down 4.2% over 20 days and sits at the 28th percentile of its 1-year range — a mild tailwind via lower energy costs.',
      "Intel's priors for oil exposure are low (0.3); the semiconductor sector is not a major direct oil consumer.",
      'Lower energy costs modestly reduce fab operating expenses, but the effect is secondary to the leadership disruption.',
    ],
    math: {
      formula: 's = d × tanh(z / 2)',
      inputs: { z: 0.48, rho: 0.12, d: 1 },
      contribution: 0.02,
    },
    sources: [
      { name: 'FRED DCOILWTICO', url: 'https://fred.stlouisfed.org/series/DCOILWTICO', retrieved_at: '2024-12-02T14:01:06Z' },
    ],
    warnings: [],
  },
  {
    id: 'C4',
    title: 'Market Regime & Volatility',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:09Z',
    latency_ms: 523,
    headline: { label: 'VIX', value: 13.4, unit: '', delta: -1.2 },
    metrics: [
      { name: 'SPY 20d return', value: 3.1, unit: '%' },
      { name: 'SPY 60d return', value: 7.4, unit: '%' },
      { name: 'SPY vs 200d MA', value: 7.2, unit: '%' },
      { name: 'VIX level', value: 13.4, unit: '' },
      { name: 'VIX percentile (1y)', value: 18, unit: '%ile' },
      { name: 'INTC beta (1y)', value: 0.82, unit: '' },
    ],
    series: makeSeries(60, 14.5, 0.04),
    signal: 0.44,
    label: 'tailwind',
    weight: 0.7,
    quality: 0.98,
    reasoning: [
      'VIX at 13.4 is in the 18th percentile of its 1-year distribution — a low-fear, risk-on environment.',
      'SPY is up 3.1% over 20 days and trading 7.2% above its 200-day moving average, confirming a bull-market regime.',
      "In this backdrop, idiosyncratic shocks (like a CEO exit) tend to be absorbed faster than in bear markets.",
      "Intel's beta of 0.82 means it moves less than the market on average; the calm macro backdrop limits further contagion.",
    ],
    math: {
      formula: 's = d × tanh(z / 2)',
      inputs: { z: 1.5, rho: 0.61, d: 1 },
      contribution: 0.17,
    },
    sources: [
      { name: 'FRED VIXCLS', url: 'https://fred.stlouisfed.org/series/VIXCLS', retrieved_at: '2024-12-02T14:01:08Z' },
      { name: 'yfinance SPY', url: 'https://finance.yahoo.com/quote/SPY', retrieved_at: '2024-12-02T14:01:08Z' },
    ],
    warnings: [],
  },
  {
    id: 'C5',
    title: 'Sector Relative Strength',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:11Z',
    latency_ms: 445,
    headline: { label: 'INTC vs XLK (20d)', value: -6.4, unit: '%' },
    metrics: [
      { name: 'INTC 5d', value: -3.2, unit: '%' },
      { name: 'INTC 20d', value: -11.8, unit: '%' },
      { name: 'INTC 60d', value: -18.4, unit: '%' },
      { name: 'XLK 20d', value: -5.4, unit: '%' },
      { name: 'SPY 20d', value: 3.1, unit: '%' },
      { name: 'Driver classification', value: 'Company-driven', unit: '' },
    ],
    series: makeSeries(60, 24, 0.03),
    signal: -0.72,
    label: 'headwind',
    weight: 0.75,
    quality: 0.97,
    reasoning: [
      'INTC has underperformed XLK by 6.4% and SPY by 14.9% over 20 days — a large company-specific gap.',
      "The underperformance classification is 'company-driven': sector and market are both positive, so the drag is INTC-specific.",
      "This pattern pre-dates the CEO announcement and intensified on the news, confirming the market had concerns about Intel's execution.",
      "Persistent relative weakness over 60 days (-18.4% vs benchmark) suggests deteriorating investor confidence in Intel's turnaround thesis.",
    ],
    math: {
      formula: 's = clip(alpha_vs_sector / threshold, -1, 1)',
      inputs: { alpha_vs_sector: -6.4, alpha_vs_spy: -14.9, threshold: 5.0 },
      contribution: -0.24,
    },
    sources: [
      { name: 'yfinance INTC', url: 'https://finance.yahoo.com/quote/INTC', retrieved_at: '2024-12-02T14:01:10Z' },
      { name: 'yfinance XLK', url: 'https://finance.yahoo.com/quote/XLK', retrieved_at: '2024-12-02T14:01:10Z' },
    ],
    warnings: [],
  },
  {
    id: 'C6',
    title: 'Cross-Sector Dependency',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:14Z',
    latency_ms: 611,
    headline: { label: 'Linked sectors (20d avg)', value: -1.4, unit: '%' },
    metrics: [
      { name: 'SMH 20d', value: -4.1, unit: '%' },
      { name: 'XLY 20d', value: 1.2, unit: '%' },
      { name: 'XLI 20d', value: 0.8, unit: '%' },
      { name: 'Corr INTC-SMH (252d)', value: 0.68, unit: '' },
    ],
    series: makeSeries(60, 215, 0.025),
    signal: -0.31,
    label: 'headwind',
    weight: 0.65,
    quality: 0.88,
    reasoning: [
      'The semiconductor ETF (SMH) is down 4.1% over 20 days, dragging linked nodes.',
      "Intel's 252-day correlation with SMH is 0.68 — moderate co-movement means sector weakness compounds company headwinds.",
      'Downstream customers (auto, industrial via XLY/XLI) show mild strength, limiting contagion beyond the chip sector.',
      'The GM→chips dependency edge is active but weak; auto demand is not an immediate amplifier here.',
    ],
    math: {
      formula: 's = sum(strength_i × move_i × sign_i) / n, clipped to [-1,1]',
      inputs: { smh_move: -4.1, smh_strength: 0.75, xly_move: 1.2, xly_strength: 0.3 },
      contribution: -0.09,
    },
    sources: [
      { name: 'yfinance SMH', url: 'https://finance.yahoo.com/quote/SMH', retrieved_at: '2024-12-02T14:01:12Z' },
      { name: 'data/dependencies.json (curated)', url: '', retrieved_at: '2024-12-02T14:01:12Z' },
    ],
    warnings: ['Dependency edges are curated judgment; citations TODO.'],
  },
  {
    id: 'C7',
    title: 'Geopolitical & Policy Risk',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:16Z',
    latency_ms: 374,
    headline: { label: 'GPR Index', value: 118.4, unit: '', delta: 8.2 },
    metrics: [
      { name: 'GPR level', value: 118.4, unit: '' },
      { name: 'GPR 1y percentile', value: 61, unit: '%ile' },
      { name: 'GPR 3m change', value: 8.2, unit: '' },
      { name: 'INTC geopolitical exposure', value: 'High', unit: '' },
    ],
    series: makeSeries(60, 110, 0.015),
    signal: -0.55,
    label: 'headwind',
    weight: 0.78,
    quality: 0.85,
    reasoning: [
      'The Caldara-Iacoviello GPR index stands at 118.4 — 61st percentile — with an 8-point rise over 3 months.',
      "Intel has a high geopolitical exposure prior (0.7): export controls on chips to China remain a live regulatory risk, and Intel's new Foundry Services ambitions depend on government subsidies (CHIPS Act).",
      'A leadership vacuum at the top magnifies policy execution risk — investors may question whether Intel can navigate subsidy negotiations without continuity.',
      'Elevated GPR modestly amplifies sector headwinds already present in C5.',
    ],
    math: {
      formula: 's = d × tanh(z / 2), w = max(|rho|/0.5, w_prior)',
      inputs: { z: -1.8, rho: -0.41, d: -1, w_prior: 0.7 },
      contribution: -0.19,
    },
    sources: [
      { name: 'GPR Index (Caldara & Iacoviello 2022)', url: 'https://www.matteoiacoviello.com/gpr.htm', retrieved_at: '2024-12-02T14:01:15Z' },
    ],
    warnings: ['Recent GPR values are preliminary and subject to revision.'],
  },
  {
    id: 'C8',
    title: 'Financial Health',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:21Z',
    latency_ms: 892,
    headline: { label: 'Interest Coverage', value: 2.1, unit: 'x', delta: -1.4 },
    metrics: [
      { name: 'Current ratio', value: 1.42, unit: 'x' },
      { name: 'Debt/Equity', value: 0.52, unit: 'x' },
      { name: 'Interest coverage', value: 2.1, unit: 'x' },
      { name: 'Operating margin', value: 1.8, unit: '%' },
      { name: 'Cash', value: 24.1, unit: '$B' },
    ],
    series: makeSeries(12, 4.2, 0.08),
    signal: -0.61,
    label: 'headwind',
    weight: 0.78,
    quality: 0.91,
    reasoning: [
      "Interest coverage of 2.1x sits in the 'weak' band (threshold: <2 weak, >5 strong) — the blended score (absolute + 5y percentile) is -0.61.",
      "Operating margin at 1.8% is severely compressed versus Intel's historical range of 25–35%, reflecting factory underutilisation.",
      'The current ratio (1.42x) and cash position ($24.1B) provide near-term liquidity buffer, but deteriorating margins limit self-funding capacity.',
      'A CEO transition creates uncertainty about capital allocation — will the new leader continue the foundry investment or pivot? Markets dislike this ambiguity.',
    ],
    math: {
      formula: 's = 0.5 × band_score + 0.5 × pct_vs_5y, clipped [-1,1]',
      inputs: { interest_coverage: 2.1, band_score: -0.6, pct_vs_5y: 0.08 },
      contribution: -0.21,
    },
    sources: [
      { name: 'SEC EDGAR XBRL (CIK 0000050863)', url: 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000050863.json', retrieved_at: '2024-12-02T14:01:18Z' },
    ],
    warnings: ['Operating margin reflects TTM through Q3 2024 10-Q (filed 2024-10-25).'],
  },
  {
    id: 'C9',
    title: 'Earnings & Growth',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:24Z',
    latency_ms: 756,
    headline: { label: 'Revenue YoY', value: -6.2, unit: '%' },
    metrics: [
      { name: 'Revenue YoY', value: -6.2, unit: '%' },
      { name: 'Diluted EPS YoY', value: -88.4, unit: '%' },
      { name: 'Gross margin trend', value: 'Declining', unit: '' },
      { name: 'Last earnings abnormal return', value: -9.4, unit: '%' },
    ],
    series: makeSeries(8, 54, 0.05),
    signal: -0.78,
    label: 'headwind',
    weight: 0.8,
    quality: 0.93,
    reasoning: [
      'Revenue has declined 6.2% YoY; diluted EPS is down 88% — the earnings deterioration is severe and accelerating.',
      'The last earnings-day abnormal return was -9.4% (stock minus SPY on Q3 2024 earnings day), confirming the market was surprised by weak execution.',
      'Margin compression is structural, not cyclical: Intel is absorbing high fixed costs from new fabs that are not yet at scale.',
      'A CEO change typically precedes a kitchen-sink quarter where the incoming leader resets expectations downward.',
    ],
    math: {
      formula: 's = clip(0.4×rev_score + 0.4×eps_score + 0.2×abn_ret_score, -1,1)',
      inputs: { rev_yoy: -6.2, eps_yoy: -88.4, abnormal_return: -9.4 },
      contribution: -0.28,
    },
    sources: [
      { name: 'SEC EDGAR XBRL (CIK 0000050863)', url: 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000050863.json', retrieved_at: '2024-12-02T14:01:22Z' },
      { name: 'yfinance INTC', url: 'https://finance.yahoo.com/quote/INTC', retrieved_at: '2024-12-02T14:01:22Z' },
    ],
    warnings: [],
  },
  {
    id: 'C10',
    title: 'Valuation & Price Momentum',
    status: 'done',
    as_of: '2024-12-02',
    fetched_at: '2024-12-02T14:01:26Z',
    latency_ms: 534,
    headline: { label: 'P/E (TTM)', value: 94.2, unit: 'x', delta: 68.1 },
    metrics: [
      { name: 'P/E TTM', value: 94.2, unit: 'x' },
      { name: 'P/E 5y percentile', value: 89, unit: '%ile' },
      { name: '52-week range position', value: 14, unit: '%' },
      { name: '50d MA trend', value: 'Below', unit: '' },
      { name: '200d MA trend', value: 'Below', unit: '' },
    ],
    series: makeSeries(60, 42, 0.025),
    signal: -0.52,
    label: 'headwind',
    weight: 0.75,
    quality: 0.96,
    reasoning: [
      "P/E of 94x is misleading (near-zero earnings in numerator); the 89th percentile on a 5y basis signals the stock is not 'cheap' despite price declines.",
      'Trading at the 14th percentile of its 52-week range means the stock has already fallen significantly, limiting further momentum selling — but no floor is visible.',
      'Price is below both 50-day and 200-day moving averages — a confirmed bearish technical setup.',
      'Momentum headwind is consistent with the fundamental picture: until a credible plan emerges from new leadership, re-rating is unlikely.',
    ],
    math: {
      formula: 's = 0.5×pe_pct_score + 0.3×range_score + 0.2×ma_score, clipped [-1,1]',
      inputs: { pe_pct: 89, range_pct: 14, below_50ma: true, below_200ma: true },
      contribution: -0.17,
    },
    sources: [
      { name: 'SEC EDGAR XBRL (CIK 0000050863)', url: 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000050863.json', retrieved_at: '2024-12-02T14:01:25Z' },
      { name: 'yfinance INTC', url: 'https://finance.yahoo.com/quote/INTC', retrieved_at: '2024-12-02T14:01:25Z' },
    ],
    warnings: [],
  },
]

export const MOCK_AGGREGATE: AggregateResult = {
  composite_signal: -0.52,
  evidence_strength: 0.74,
  coverage: 0.88,
  scenarios: [
    {
      name: 'Tailwind-dominant',
      score: 0.08,
      ci_low: 0.03,
      ci_high: 0.16,
      rationale: 'Low VIX and positive market regime provide some macro support.',
      watch_for: 'VIX spike above 20 would remove this scenario.',
    },
    {
      name: 'Mixed',
      score: 0.21,
      ci_low: 0.14,
      ci_high: 0.30,
      rationale: 'Calm macro offsets company-specific pressures partially.',
      watch_for: 'New CEO announcement with credible plan could shift balance.',
    },
    {
      name: 'Headwind-dominant',
      score: 0.71,
      ci_low: 0.62,
      ci_high: 0.80,
      rationale: 'Company fundamentals (C8, C9), sector weakness (C5), and policy risk (C7) dominate.',
      watch_for: 'Kitchen-sink guidance cut likely within 60 days.',
    },
  ],
  card_contributions: {
    C1: -0.09, C2: -0.14, C3: 0.02, C4: 0.17,
    C5: -0.24, C6: -0.09, C7: -0.19, C8: -0.21,
    C9: -0.28, C10: -0.17,
  },
}

export const MOCK_VERDICT: VerdictOutput = {
  headline: "Intel's evidence after the event is negative",
  answer: "After the chief executive change you described, the current evidence for Intel leans negative. Over the next 20 days, the evidence leans negative, not toward a definite outcome. Sales and profit trends and the company's financial strength are the strongest findings working against Intel. The interest rate and inflation check also points against the company, while the available findings do not establish that the leadership change caused any of these results.",
  how_sure_level: 'Medium',
  how_sure_reason: 'Most checks returned data, though some measures are incomplete and the findings do not all agree.',
  points: [
    { title: 'Sales and profit trend', explanation: 'Sales changed minus 6.2% compared with a year ago, and profit per share changed minus 88% compared with a year ago. This points against the company with a strong reading.', findings: ['C9'], direction: 'against', strength: 'strong' },
    { title: 'Financial strength', explanation: 'The available filing measures show pressure in the company’s financial position. This points against the company with a strong reading.', findings: ['C8'], direction: 'against', strength: 'strong' },
    { title: 'Compared with its industry', explanation: 'Intel’s share price changed minus 6.4% over 20 trading days, while its industry changed 8.5%. This points against the company with a strong reading.', findings: ['C5'], direction: 'against', strength: 'strong' },
    { title: 'Interest rates and inflation', explanation: 'The long term United States government borrowing rate is 4.21%, after changing by 12 basis points over 20 trading days. Prices rose 2.6% compared with a year ago. This points against the company with a moderate reading.', findings: ['C2'], direction: 'against', strength: 'moderate' },
    { title: 'United States dollar strength', explanation: 'The United States dollar changed 1.8% over the past 20 trading days and 3.4% over the past 60 trading days. This points against the company with a moderate reading.', findings: ['C1'], direction: 'against', strength: 'moderate' },
    { title: 'Market mood', explanation: 'The wider share market remained unsettled over the measured period. This points against the company with a slight reading.', findings: ['C4'], direction: 'against', strength: 'slight' },
    { title: 'Price and valuation', explanation: 'The share price is below its recent average prices, while the company profit comparison is mixed. This points against the company with a slight reading.', findings: ['C10'], direction: 'against', strength: 'slight' },
  ],
  unknowns: [
    'These checks cannot establish whether the chief executive change caused later share price moves.',
    'They cannot show what company leaders will do next or whether future results will improve.',
    'They do not measure every supplier, customer, or decision that could affect the company.',
  ],
  watch: [
    { what: 'Sales and profit trend', why: 'New company reports can show whether sales and profit per share continue to change.', findings: ['C9'] },
    { what: 'Financial strength', why: 'Later company filings can add information about assets, debt, and costs.', findings: ['C8'] },
    { what: 'Compared with its industry', why: 'The comparison can show whether the company continues to move differently from similar companies.', findings: ['C5'] },
  ],
  scenarios: [
    { id: 'against', name: 'Things get harder', score: 0.71, what_it_looks_like: 'The findings that work against the company remain more important.', signs: 'Sales and profit trends or financial strength remain weak.' },
    { id: 'mixed', name: 'A mixed picture', score: 0.21, what_it_looks_like: 'Findings continue to point in different directions.', signs: 'Some company measures improve while other findings remain difficult.' },
    { id: 'for', name: 'Things improve', score: 0.08, what_it_looks_like: 'The findings that support the company become more important.', signs: 'New company reports show improvement in sales, profit, or financial strength.' },
  ],
  scenario_split: { against: 0.71, mixed: 0.21, for: 0.08 },
  summary: "After the chief executive change you described, the current evidence for Intel leans negative. Over the next 20 days, the evidence leans negative, not toward a definite outcome.",
  key_drivers: [
    { card: 'C9', point: 'Revenue -6.2% YoY and EPS -88% with no visible inflection; last earnings surprise was -9.4% abnormal return.' },
    { card: 'C8', point: 'Interest coverage of 2.1x and operating margin of 1.8% signal structural stress in the foundry transition.' },
    { card: 'C5', point: 'INTC has underperformed XLK by 6.4% and SPY by 14.9% over 20 days — company-driven, not sector-driven.' },
    { card: 'C7', point: 'Elevated geopolitical risk (GPR 61st %ile) compounds export-control uncertainty and CHIPS Act execution risk.' },
  ],
  counter_evidence: [
    { card: 'C4', point: 'VIX at the 18th percentile signals a low-fear market environment that historically accelerates recovery from idiosyncratic shocks.' },
    { card: 'C3', point: 'Softening oil prices modestly reduce fab energy costs, a small offset to margin pressure.' },
  ],
  references: [
    { name: 'SEC EDGAR XBRL (CIK 0000050863)', url: 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000050863.json', retrieved_at: '2024-12-02T14:01:25Z' },
    { name: 'FRED DTWEXBGS', url: 'https://fred.stlouisfed.org/series/DTWEXBGS', retrieved_at: '2024-12-02T14:01:00Z' },
    { name: 'GPR Index (Caldara & Iacoviello 2022)', url: 'https://www.matteoiacoviello.com/gpr.htm', retrieved_at: '2024-12-02T14:01:15Z' },
    { name: 'yfinance INTC', url: 'https://finance.yahoo.com/quote/INTC', retrieved_at: '2024-12-02T14:01:22Z' },
  ],
  is_fallback: true,
  model_used: 'template (demo mode)',
  is_fallback_model: false,
}

export interface ExampleQuery {
  label: string
  chipLabel: string
  query: string
  as_of: string
  ticker: string
}

export const EXAMPLE_QUERIES: ExampleQuery[] = [
  { label: 'Intel leadership change', chipLabel: 'Intel leadership change', query: "Intel's chief executive just left. What do the available findings show?", as_of: '2024-12-02', ticker: 'INTC' },
  { label: 'Oil price change', chipLabel: 'Oil prices and ExxonMobil', query: 'Oil prices are rising. What do the available findings show for ExxonMobil?', as_of: '2022-02-25', ticker: 'XOM' },
  { label: 'Banking disruption', chipLabel: 'Banking changes and JPMorgan Chase', query: 'A large bank has failed. What do the available findings show for JPMorgan Chase?', as_of: '2023-03-13', ticker: 'JPM' },
  { label: 'Nvidia share price change', chipLabel: 'Nvidia compared with its industry', query: 'Nvidia shares fell after new artificial intelligence news. How did the company compare with its industry?', as_of: '2025-01-28', ticker: 'NVDA' },
]
