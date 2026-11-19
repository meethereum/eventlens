// Company name, description, and sector for every covered ticker.

export interface CompanyInfo {
  name: string
  shortName: string
  sector: string
  description: string
}

export const COMPANIES: Record<string, CompanyInfo> = {
  NVDA: { name: 'Nvidia',         shortName: 'Nvidia',       sector: 'Technology',             description: 'AI chips & graphics processors' },
  INTC: { name: 'Intel',          shortName: 'Intel',        sector: 'Technology',             description: 'Semiconductor manufacturer' },
  AAPL: { name: 'Apple',          shortName: 'Apple',        sector: 'Technology',             description: 'Consumer electronics & software' },
  MSFT: { name: 'Microsoft',      shortName: 'Microsoft',    sector: 'Technology',             description: 'Cloud computing & software' },
  GM:   { name: 'General Motors', shortName: 'GM',           sector: 'Consumer Discretionary', description: 'Automaker' },
  SBUX: { name: 'Starbucks',      shortName: 'Starbucks',    sector: 'Consumer Discretionary', description: 'Global coffee chain' },
  AMZN: { name: 'Amazon',         shortName: 'Amazon',       sector: 'Consumer Discretionary', description: 'E-commerce & cloud (AWS)' },
  DIS:  { name: 'Disney',         shortName: 'Disney',       sector: 'Communication Services', description: 'Entertainment & streaming' },
  BA:   { name: 'Boeing',         shortName: 'Boeing',       sector: 'Industrials',            description: 'Commercial & defense aircraft' },
  RTX:  { name: 'RTX',            shortName: 'RTX',          sector: 'Industrials',            description: 'Defense & aerospace systems' },
  XOM:  { name: 'ExxonMobil',     shortName: 'Exxon',        sector: 'Energy',                 description: 'Integrated oil & gas' },
  CVX:  { name: 'Chevron',        shortName: 'Chevron',      sector: 'Energy',                 description: 'Integrated oil & gas' },
  JPM:  { name: 'JPMorgan Chase', shortName: 'JPMorgan',     sector: 'Financials',             description: 'Largest US bank' },
  SCHW: { name: 'Charles Schwab', shortName: 'Schwab',       sector: 'Financials',             description: 'Brokerage & wealth management' },
  UNH:  { name: 'UnitedHealth',   shortName: 'UnitedHealth', sector: 'Health Care',            description: 'Health insurance & services' },
}

export function companyName(ticker: string, style: 'full' | 'short' = 'full'): string {
  const info = COMPANIES[ticker?.toUpperCase()]
  if (!info) return ticker
  return style === 'short' ? info.shortName : info.name
}

export function companyInfo(ticker: string): CompanyInfo | null {
  return COMPANIES[ticker?.toUpperCase()] ?? null
}

// Card display names — no emojis, no C1/C2 codes
export const CARD_DISPLAY: Record<string, { name: string; description: string }> = {
  C1:  { name: 'Dollar Strength',       description: 'How strong the US dollar is right now'         },
  C2:  { name: 'Interest Rates',        description: 'What the Fed is doing with rates & inflation'   },
  C3:  { name: 'Oil Prices',            description: 'Where crude oil is trading and its trend'       },
  C4:  { name: 'Market Mood',           description: 'Is the overall stock market calm or fearful?'   },
  C5:  { name: 'vs Competitors',        description: 'How the stock is performing vs its sector'      },
  C6:  { name: 'Supply Chain Links',    description: 'Who depends on whom — suppliers & customers'   },
  C7:  { name: 'Political Risk',        description: 'Wars, sanctions, and policy uncertainty'        },
  C8:  { name: 'Financial Health',      description: 'Balance sheet strength, debt, and cash'         },
  C9:  { name: 'Earnings & Growth',     description: 'Revenue growth, profit, and earnings surprises' },
  C10: { name: 'Valuation',             description: 'Is the stock cheap or expensive vs history?'    },
  C11: { name: 'Historical Precedents', description: 'Similar events in the past and what happened'   },
}

export function cardDisplayName(cardId: string): string {
  return CARD_DISPLAY[cardId]?.name ?? cardId
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
