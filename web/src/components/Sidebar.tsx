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
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CardOutput } from '@/types'
import { cardDisplayName, companyName, companyNamesInText } from '@/lib/companies'

export type TabId = 'verdict' | 'simulator' | 'precedents' | 'cards' | 'all'

interface Props {
  ticker?: string
  eventType?: string
  compositeSignal?: number
  cards: Record<string, CardOutput>
  activeTab: TabId
  onSelectTab: (tab: TabId) => void
  onCardClick: (card: CardOutput) => void
  collapsed: boolean
  onToggleCollapse: () => void
}

const TABS: Array<{ id: TabId; label: string; icon: typeof FileText }> = [
  { id: 'verdict', label: 'Overview', icon: FileText },
  { id: 'simulator', label: 'Sensitivity analysis', icon: Sliders },
  { id: 'precedents', label: 'Past examples', icon: TrendingUp },
  { id: 'cards', label: 'Evidence factors', icon: LayoutGrid },
  { id: 'all', label: 'Complete analysis', icon: Layers },
]

const ORDERED_CARD_IDS = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10']

export default function Sidebar({
  ticker,
  eventType,
  compositeSignal,
  cards,
  activeTab,
  onSelectTab,
  onCardClick,
  collapsed,
  onToggleCollapse,
}: Props) {
  const displayCompany = ticker ? companyName(ticker) : 'Company analysis'
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
        'w-full lg:w-72',
        collapsed && 'lg:w-14',
      )}
    >
      <div className="rounded-2xl border border-border/70 bg-surface-1/95 backdrop-blur-md shadow-lg overflow-hidden flex flex-col lg:sticky lg:top-20 lg:max-h-[calc(100dvh-6rem)]">
        {/* Sidebar Header */}
        <div className="p-3.5 border-b border-border/60 flex items-center justify-between gap-2">
          <div className={cn('min-w-0', collapsed && 'lg:hidden')}>
              <span className="text-base font-semibold text-text-primary truncate">
                {displayCompany}
              </span>
              {eventType && (
                <p className="text-base text-text-secondary truncate mt-1" title={companyNamesInText(eventType)}>
                  {companyNamesInText(eventType)}
                </p>
              )}
          </div>
          {collapsed && (
            <span className="font-bold text-2xs text-accent-glow mx-auto">
              {displayCompany.slice(0, 1)}
            </span>
          )}

          <button
            type="button"
            onClick={onToggleCollapse}
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            className="hidden lg:flex p-1.5 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-surface-3 transition-colors shrink-0"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Overall Direction Banner (Expanded only) */}
        {!collapsed && direction && (
          <div
            className={cn(
              'px-3.5 py-2.5 border-b text-base flex items-center justify-between font-medium',
              direction === 'positive' && 'bg-tailwind/10 text-tailwind border-tailwind/20',
              direction === 'negative' && 'bg-headwind/10 text-headwind border-headwind/20',
              direction === 'mixed' && 'bg-amber/10 text-amber border-amber/20',
            )}
          >
            <div className="flex items-center gap-1.5">
              {direction === 'positive' && <TrendingUp className="w-4 h-4" />}
              {direction === 'negative' && <TrendingDown className="w-4 h-4" />}
              {direction === 'mixed' && <Minus className="w-4 h-4" />}
              <span className="capitalize">{direction} evidence balance</span>
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
                  'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-base font-medium transition-all text-left',
                  isActive
                    ? 'bg-accent/15 text-accent-glow border border-accent/30 shadow-sm'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-2 border border-transparent',
                  collapsed && 'lg:justify-center lg:px-1.5',
                )}
              >
                <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-accent-glow' : 'text-text-muted')} />
                  <div className={cn('flex-1 flex items-center justify-between min-w-0', collapsed && 'lg:hidden')}>
                    <span className="truncate">{tab.label}</span>
                  </div>
              </button>
            )
          })}
        </div>

        {/* Evidence-factor list */}
        <div className="hidden flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin lg:block">
          {!collapsed ? (
            <div className="flex items-center justify-between px-2 py-1.5 text-base font-semibold text-text-secondary">
                <span>Evidence factors</span>
              <span className="font-mono">{doneCardsCount}/10 ready</span>
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
                  title={name}
                  className="w-full flex items-center justify-center py-2 rounded-lg hover:bg-surface-2 transition-colors relative group"
                >
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
                  <span className="truncate text-text-secondary group-hover:text-text-primary text-base">
                    {companyNamesInText(card?.plain_title || name)}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {isDone && card && (
                    <span
                      className={cn('h-2.5 w-2.5 rounded-full border', labelColor)}
                      aria-label={label === 'tailwind' ? 'Positive finding' : label === 'headwind' ? 'Negative finding' : 'Neutral finding'}
                    />
                  )}
                  {isFetching && (
                    <span className="w-2 h-2 rounded-full bg-accent-glow animate-pulse" />
                  )}
                </div>
              </button>
            )
          })}

        </div>
      </div>
    </aside>
  )
}
