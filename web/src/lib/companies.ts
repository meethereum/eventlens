// Company name, description, and sector for every covered ticker.

export interface CompanyInfo {
  name: string
  shortName: string
  sector: string
  description: string
}

export const COMPANIES: Record<string, CompanyInfo> = {
  NVDA: { name: 'Nvidia',         shortName: 'Nvidia',       sector: 'Technology',             description: 'Computer chips and graphics processors' },
  INTC: { name: 'Intel',          shortName: 'Intel',        sector: 'Technology',             description: 'Semiconductor manufacturer' },
  AAPL: { name: 'Apple',          shortName: 'Apple',        sector: 'Technology',             description: 'Consumer electronics & software' },
  MSFT: { name: 'Microsoft',      shortName: 'Microsoft',    sector: 'Technology',             description: 'Cloud computing & software' },
  GM:   { name: 'General Motors', shortName: 'General Motors', sector: 'Consumer Discretionary', description: 'Automaker' },
  SBUX: { name: 'Starbucks',      shortName: 'Starbucks',    sector: 'Consumer Discretionary', description: 'Global coffee chain' },
  AMZN: { name: 'Amazon',         shortName: 'Amazon',       sector: 'Consumer Discretionary', description: 'Online shopping and cloud services' },
  DIS:  { name: 'Disney',         shortName: 'Disney',       sector: 'Communication Services', description: 'Entertainment & streaming' },
  BA:   { name: 'Boeing',         shortName: 'Boeing',       sector: 'Industrials',            description: 'Commercial & defense aircraft' },
  RTX:  { name: 'Raytheon',       shortName: 'Raytheon',     sector: 'Industrials',            description: 'Defense and aerospace systems' },
  XOM:  { name: 'ExxonMobil',     shortName: 'Exxon',        sector: 'Energy',                 description: 'Integrated oil & gas' },
  CVX:  { name: 'Chevron',        shortName: 'Chevron',      sector: 'Energy',                 description: 'Integrated oil & gas' },
  JPM:  { name: 'JPMorgan Chase', shortName: 'JPMorgan Chase', sector: 'Financials',           description: 'Banking and financial services' },
  SCHW: { name: 'Charles Schwab', shortName: 'Charles Schwab', sector: 'Financials',           description: 'Investing and financial services' },
  UNH:  { name: 'UnitedHealth Group', shortName: 'UnitedHealth Group', sector: 'Health Care', description: 'Health coverage and care services' },
}

export function companyName(ticker: string, style: 'full' | 'short' = 'full'): string {
  const info = COMPANIES[ticker?.toUpperCase()]
  if (!info) return 'Company not covered'
  return style === 'short' ? info.shortName : info.name
}

export function companyInfo(ticker: string): CompanyInfo | null {
  return COMPANIES[ticker?.toUpperCase()] ?? null
}

export function companyNamesInText(text: string): string {
  let output = Object.entries(COMPANIES)
    .sort(([left], [right]) => right.length - left.length)
    .reduce((output, [ticker, info]) => {
      const tickerPattern = ticker === 'RTX'
        ? /\bRTX\b(?!\s+Corporation\b)/gi
        : new RegExp(`\\b${ticker}\\b`, 'gi')
      return output.replace(tickerPattern, info.name)
    }, text)
  output = output.replace(/\bU\.S\./g, 'United States').replace(/\bUS\b/g, 'United States')
  const plainTerms: Array<[RegExp, string]> = [
    [/\bCEO\b/gi, 'chief executive'],
    [/\bDXY\b/gi, 'United States dollar'], [/\bWTI\b/gi, 'oil'],
    [/\bVIX\b/gi, 'market volatility'], [/\bGPR\b/gi, 'world tension'],
    [/\bSPY\b/gi, 'the broad United States market'], [/\bCPI\b/gi, 'prices'],
    [/\bEPS\b/gi, 'profit per share'], [/\bYoY\b/gi, 'compared with a year ago'],
    [/\bbp\b/gi, 'basis points'], [/\bpp\b/gi, 'percentage points'],
    [/\bMA\b/gi, 'average price'], [/\bAI\b/gi, 'artificial intelligence'],
    [/\bLLM\b/gi, 'language model'], [/\bSEC\b/gi, 'company filing'],
    [/\bFRED\b/gi, 'public data'],
    [/\bSVB\b/gi, 'a large bank'], [/\bTTM\b/gi, 'the latest year'],
    [/\bCET1\b/gi, "bank owners' funds"], [/\bS&P\b/g, 'United States share market'],
  ]
  for (const [pattern, replacement] of plainTerms) output = output.replace(pattern, replacement)
  const internalLabels: Array<[RegExp, string]> = [
    [/\bC10\b/g, 'factor ten'], [/\bC([1-9])\b/g, 'factor $1'],
    [/\bSMH\b/g, 'chip makers'], [/\bTSM\b/g, 'Taiwan Semiconductor Manufacturing'],
    [/\bCRWD\b/g, 'cybersecurity companies'], [/\bSPR\b/g, 'aircraft parts makers'],
    [/\bXLE\b/g, 'energy companies'], [/\bXLY\b/g, 'consumer companies'],
    [/\bXLI\b/g, 'industrial companies'], [/\bKRE\b/g, 'regional banks'],
    [/\bITA\b/g, 'defense companies'],
    [/\bDGS10\b/g, 'long term government borrowing rate'],
    [/\bT10Y2Y\b/g, 'difference between long and short term borrowing rates'],
    [/\bDFF\b/g, 'United States policy interest rate'],
    [/\bCPIAUCSL\b/g, 'United States price measure'],
    [/\bDCOILWTICO\b/g, 'United States oil price series'],
    [/\bDCOILBRENTEU\b/g, 'world oil price series'],
    [/\bVIXCLS\b/g, 'market volatility series'],
    [/\bUSEPUINDXD\b/g, 'United States policy uncertainty series'],
    [/\bXBRL\b/g, 'company filing data'], [/\bCIK\b/g, 'company filing identifier'],
  ]
  for (const [pattern, replacement] of internalLabels) output = output.replace(pattern, replacement)
  output = output.replace(/\b[A-Z]{2,}\b/g, match => match.toLowerCase())
  return output.replace(/[\-‐‑‒–—―−]+/g, ',').replace(/\s+/g, ' ').trim()
}

// Evidence-factor display names — internal IDs are never shown as labels.
export const CARD_DISPLAY: Record<string, { name: string; description: string }> = {
  C1:  { name: 'United States dollar strength', description: 'Changes in the value of the United States dollar' },
  C2:  { name: 'Interest rates and inflation', description: 'Government borrowing costs and price changes' },
  C3:  { name: 'Oil prices', description: 'Oil prices and recent changes' },
  C4:  { name: 'Market mood', description: 'Broad share market changes and volatility' },
  C5:  { name: 'Compared with its industry', description: 'Company share changes compared with its industry and wider market' },
  C6:  { name: 'Links to other industries', description: 'Selected business links to other industries' },
  C7:  { name: 'World tension and policy risk', description: 'Measures of world tension and policy uncertainty' },
  C8:  { name: 'Financial strength', description: 'Company assets, debt, costs, and profit' },
  C9:  { name: 'Sales and profit trend', description: 'Sales and profit per share compared with a year ago' },
  C10: { name: 'Price and valuation', description: 'Share price compared with company profit and recent prices' },
}

export function cardDisplayName(cardId: string): string {
  return CARD_DISPLAY[cardId]?.name ?? 'Unknown evidence factor'
}

export function cardDescription(cardId: string): string {
  return CARD_DISPLAY[cardId]?.description ?? ''
}

// No-op kept for backward compat — returns empty string
export function cardIcon(): string {
  return ''
}

export function signalText(label: string, ticker?: string): {
  headline: string
  detail: string
  color: 'green' | 'red' | 'gray'
} {
  const name = ticker ? companyName(ticker, 'short') : 'this'
  switch (label) {
    case 'tailwind':
      return { headline: 'Working in its favor', detail: `This factor is a positive for ${name}`, color: 'green' }
    case 'headwind':
      return { headline: 'Working against it',   detail: `This factor is a negative for ${name}`, color: 'red' }
    default:
      return { headline: 'Not a major factor',   detail: 'Limited impact either way',              color: 'gray' }
  }
}
