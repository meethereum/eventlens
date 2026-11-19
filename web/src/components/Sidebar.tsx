import { useState } from 'react'
import {
  FileText,
  Sliders,
  TrendingUp,
  TrendingDown,
  Minus,
  LayoutGrid,
  Layers,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  ShieldAlert,
  Lock,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CardOutput } from '@/types'
import { cardDisplayName, companyName } from '@/lib/companies'

export type TabId = 'verdict' | 'simulator' | 'precedents' | 'cards' | 'all'

interface Props {
  ticker?: string
  asOf?: string
  eventType?: string
  compositeSignal?: number
  phase: string
  cards: Record<string, CardOutput>
  activeTab: TabId
  onSelectTab: (tab: TabId) => void
  onCardClick: (card: CardOutput) => void
  collapsed: boolean
  onToggleCollapse: () => void
}

const TABS: Array<{ id: TabId; label: string; icon: typeof FileText; badge?: string }> = [
  { id: 'verdict', label: 'Executive Verdict', icon: FileText, badge: 'Analysis' },
  { id: 'simulator', label: 'What-If Lab', icon: Sliders, badge: 'Live Math' },
  { id: 'precedents', label: 'Precedent Analogs', icon: TrendingUp, badge: 'AI Cohort' },
  { id: 'cards', label: 'Evidence Grid', icon: LayoutGrid },
  { id: 'all', label: 'Full Briefing', icon: Layers },
]

const ORDERED_CARD_IDS = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10']

export default function Sidebar({
  ticker,
  asOf,
  eventType,
  compositeSignal,
  phase,
  cards,
  activeTab,
  onSelectTab,
  onCardClick,
  collapsed,
  onToggleCollapse,
}: Props) {
  const compShort = ticker ? companyName(ticker, 'short') : ''
  const doneCardsCount = ORDERED_CARD_IDS.filter(id => cards[id]?.status === 'done').length

  const direction =
    compositeSignal !== undefined
      ? compositeSignal > 0.1
        ? 'positive'
        : compositeSignal < -0.1
          ? 'negative'
          : 'mixed'
      : null

  return (
    <aside
      className={cn(
        'transition-all duration-300 ease-in-out shrink-0 select-none',
        collapsed ? 'w-14' : 'w-72 lg:w-80',
      )}
    >
      <div className="sticky top-20 rounded-2xl border border-border/70 bg-surface-1/95 backdrop-blur-md shadow-lg overflow-hidden flex flex-col max-h-[calc(100dvh-6rem)]">
        {/* Sidebar Header */}
        <div className="p-3.5 border-b border-border/60 flex items-center justify-between gap-2">
          {!collapsed ? (
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-sm text-text-primary px-1.5 py-0.5 rounded bg-surface-3 border border-border">
                  {ticker || 'ANALYSIS'}
                </span>
                <span className="text-xs font-semibold text-text-secondary truncate">
                  {compShort}
                </span>
              </div>
              {eventType && (
                <p className="text-2xs text-text-muted truncate mt-1" title={eventType}>
                  {eventType}
                </p>
              )}
            </div>
          ) : (
            <span className="font-mono font-bold text-2xs text-accent-glow mx-auto">
              {ticker ? ticker.slice(0, 3) : 'EVT'}
            </span>
          )}

          <button
            type="button"
            onClick={onToggleCollapse}
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            className="p-1.5 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-surface-3 transition-colors shrink-0"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Overall Direction Banner (Expanded only) */}
        {!collapsed && direction && (
          <div
            className={cn(
              'px-3.5 py-2.5 border-b text-xs flex items-center justify-between font-medium',
              direction === 'positive' && 'bg-tailwind/10 text-tailwind border-tailwind/20',
              direction === 'negative' && 'bg-headwind/10 text-headwind border-headwind/20',
              direction === 'mixed' && 'bg-amber/10 text-amber border-amber/20',
            )}
          >
            <div className="flex items-center gap-1.5">
              {direction === 'positive' && <TrendingUp className="w-4 h-4" />}
              {direction === 'negative' && <TrendingDown className="w-4 h-4" />}
              {direction === 'mixed' && <Minus className="w-4 h-4" />}
              <span className="capitalize">{direction} Balance</span>
            </div>
            {compositeSignal !== undefined && (
              <span className="font-mono font-bold">
                {compositeSignal > 0 ? '+' : ''}
                {compositeSignal.toFixed(2)}
              </span>
            )}
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="p-2 border-b border-border/60 space-y-1">
          {TABS.map(tab => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id

            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onSelectTab(tab.id)}
                title={collapsed ? tab.label : undefined}
                className={cn(
                  'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-medium transition-all text-left',
                  isActive
                    ? 'bg-accent/15 text-accent-glow border border-accent/30 shadow-sm'
                    : 'text-text-muted hover:text-text-primary hover:bg-surface-2 border border-transparent',
                  collapsed && 'justify-center px-1.5',
                )}
              >
                <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-accent-glow' : 'text-text-muted')} />
                {!collapsed && (
                  <div className="flex-1 flex items-center justify-between min-w-0">
                    <span className="truncate">{tab.label}</span>
                    {tab.badge && (
                      <span className="text-2xs font-mono px-1.5 py-0.2 rounded bg-surface-3 text-text-muted border border-border/60 ml-1 shrink-0">
                        {tab.badge}
                      </span>
                    )}
                  </div>
                )}
              </button>
            )
          })}
        </div>

        {/* 10 Evidence Cards List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin">
          {!collapsed ? (
            <div className="flex items-center justify-between px-2 py-1.5 text-2xs font-semibold text-text-muted uppercase tracking-wider">
              <span>Evidence Cards</span>
              <span className="font-mono">{doneCardsCount}/10 Done</span>
            </div>
          ) : (
            <div className="h-2" />
          )}

          {ORDERED_CARD_IDS.map(cardId => {
            const card = cards[cardId]
            const name = cardDisplayName(cardId)
            const isDone = card?.status === 'done'
            const isFetching = card?.status === 'fetching'
            const label = card?.label

            const labelColor =
              label === 'tailwind'
                ? 'text-tailwind bg-tailwind-dim border-tailwind/20'
                : label === 'headwind'
                  ? 'text-headwind bg-headwind-dim border-headwind/20'
                  : 'text-neutral bg-neutral-dim border-neutral/20'

            const dotColor =
              label === 'tailwind'
                ? 'bg-tailwind'
                : label === 'headwind'
                  ? 'bg-headwind'
                  : label === 'neutral'
                    ? 'bg-amber-400'
                    : isFetching
                      ? 'bg-sky-400 animate-pulse'
                      : 'bg-surface-3'

            if (collapsed) {
              return (
                <button
                  key={cardId}
                  type="button"
                  onClick={() => card && onCardClick(card)}
                  title={`${cardId}: ${name} (${label || card?.status || 'queued'})`}
                  className="w-full flex items-center justify-center py-2 rounded-lg hover:bg-surface-2 transition-colors relative group"
                >
                  <span className="font-mono text-2xs text-text-muted group-hover:text-text-primary">
                    {cardId}
                  </span>
                  <span
                    className={cn('absolute right-1 w-1.5 h-1.5 rounded-full', dotColor)}
                  />
                </button>
              )
            }

            return (
              <button
                key={cardId}
                type="button"
                onClick={() => card && onCardClick(card)}
                disabled={!isDone}
                className={cn(
                  'w-full flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-all text-left group',
                  isDone
                    ? 'hover:bg-surface-2 cursor-pointer border border-transparent hover:border-border'
                    : 'opacity-60 cursor-default',
                )}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className={cn(
                      'font-mono text-2xs px-1 py-0.5 rounded border shrink-0',
                      isDone
                        ? 'bg-surface-3 border-border text-text-secondary group-hover:text-accent-glow'
                        : 'border-transparent text-text-muted',
                    )}
                  >
                    {cardId}
                  </span>
                  <span className="truncate text-text-secondary group-hover:text-text-primary text-xs">
                    {name}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {isDone && card && (
                    <>
                      {card.headline && (
                        <span className="font-mono text-2xs text-text-muted hidden xl:inline">
                          {typeof card.headline.value === 'number'
                            ? card.headline.value.toFixed(1)
                            : card.headline.value}
                        </span>
                      )}
                      <span
                        className={cn(
                          'text-2xs font-mono font-semibold px-1.5 py-0.2 rounded border',
                          labelColor,
                        )}
                      >
                        {card.signal > 0 ? '+' : ''}
                        {card.signal.toFixed(2)}
                      </span>
                    </>
                  )}
                  {isFetching && (
                    <span className="w-2 h-2 rounded-full bg-accent-glow animate-pulse" />
                  )}
                </div>
              </button>
            )
          })}

          {/* Locked C11 Card */}
          {!collapsed ? (
            <div className="pt-2 border-t border-border/40 px-2.5 py-1.5 flex items-center justify-between text-2xs text-text-muted opacity-60">
              <span className="flex items-center gap-1.5">
                <Lock className="w-3 h-3" />
                <span>C11 Historical Precedents</span>
              </span>
              <span className="font-mono">v2</span>
            </div>
          ) : (
            <div className="flex justify-center py-1 opacity-50" title="C11 Precedents (v2)">
              <Lock className="w-3 h-3 text-text-muted" />
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
