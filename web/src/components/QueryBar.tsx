import { useState, useRef, useEffect } from 'react'
import { Search, Loader2, X, ArrowRight } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { ParsedQuery } from '@/types'
import { EXAMPLE_QUERIES } from '@/lib/mockData'
import { companyName } from '@/lib/companies'

export interface SubmitPayload {
  query: string
  ticker: string
  as_of: string
}

interface Props {
  onSubmit: (payload: SubmitPayload) => void
  isRunning: boolean
  parsed: ParsedQuery | null
}

export default function QueryBar({ onSubmit, isRunning, parsed }: Props) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const submit = () => {
    const q = value.trim()
    if (!q || isRunning) return
    // Try to match example queries for ticker/as_of
    const example = EXAMPLE_QUERIES.find(e => e.query === q)
    onSubmit({ query: q, ticker: example?.ticker ?? '', as_of: example?.as_of ?? '' })
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="space-y-4">
      {/* Main input */}
      <div className={cn(
        'glass-panel transition-all duration-200',
        'focus-within:border-accent/50 focus-within:shadow-glow-accent',
      )}>
        <div className="flex items-start gap-3 p-3">
          <div className={cn(
            'mt-1 w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors',
            isRunning ? 'bg-accent text-white' : 'bg-surface-3 text-text-muted',
          )}>
            {isRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
          </div>

          <textarea
            ref={inputRef}
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about a company event — e.g. Intel just ousted its CEO, what should I expect?"
            rows={2}
            disabled={isRunning}
            className={cn(
              'flex-1 bg-transparent resize-none text-base text-text-primary placeholder:text-text-muted',
              'focus:outline-none leading-relaxed',
              isRunning && 'opacity-60',
            )}
          />

          <div className="flex items-center gap-2 shrink-0 mt-1">
            {value && !isRunning && (
              <button
                onClick={() => setValue('')}
                className="p-1.5 rounded-md hover:bg-surface-3 text-text-muted hover:text-text-secondary transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={submit}
              disabled={!value.trim() || isRunning}
              className={cn(
                'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                'bg-accent text-white shadow-sm',
                'hover:bg-accent-glow hover:shadow-glow-accent',
                'disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none',
              )}
            >
              Analyze
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        <div className="px-4 pb-2.5 text-xs text-text-muted">
          Press Enter to analyze · Cmd+K to focus
        </div>
      </div>

      {/* Example chips */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-text-muted self-center mr-1">Try:</span>
        {EXAMPLE_QUERIES.map(eq => (
          <button
            key={eq.label}
            onClick={() => {
              setValue(eq.query)
              onSubmit({ query: eq.query, ticker: eq.ticker, as_of: eq.as_of })
            }}
            disabled={isRunning}
            className={cn(
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs border transition-all',
              'border-border bg-surface-2 text-text-secondary',
              'hover:border-accent/40 hover:text-accent-glow hover:bg-accent-muted',
              'disabled:opacity-40 disabled:cursor-not-allowed',
            )}
          >
            {eq.chipLabel}
          </button>
        ))}
      </div>

      {/* Parsed-query summary — plain English */}
      <AnimatePresence>
        {parsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-wrap gap-2"
          >
            <ParsedChip
              label="Company"
              value={companyName(parsed.ticker) || parsed.ticker}
            />
            <ParsedChip label="Event" value={parsed.event_type} />
            {parsed.intent !== 'analysis' && (
              <ParsedChip
                label="Note"
                value={parsed.intent === 'advice_request' ? 'Advice not provided' : 'Outside scope'}
                color="amber"
              />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ParsedChip({
  label,
  value,
  color = 'default',
}: {
  label: string
  value: string
  color?: 'default' | 'accent' | 'amber'
}) {
  const styles = {
    default: 'border-border bg-surface-3 text-text-secondary',
    accent:  'border-accent/30 bg-accent-muted text-accent-glow',
    amber:   'border-amber/30 bg-amber-muted text-amber',
  }
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs border',
      styles[color],
    )}>
      <span className="text-text-muted text-2xs uppercase tracking-wide">{label}</span>
      <span className="font-medium">{value}</span>
    </span>
  )
}
