import { motion } from 'framer-motion'
import { EXAMPLE_QUERIES } from '@/lib/mockData'
import type { SubmitPayload } from '@/components/QueryBar'

interface Props {
  onSelect: (payload: SubmitPayload) => void
}

export default function EmptyState({ onSelect }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.35 }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      {/* Hero text */}
      <div className="mb-10 max-w-xl">
        <h2 className="text-2xl font-semibold text-text-primary mb-3 leading-tight">
          What's happening with a company you follow?
        </h2>
        <p className="text-base text-text-muted leading-relaxed">
          Ask a plain-English question about any company event.
          EventLens analyses 10 factors — from interest rates to supply chains —
          and explains what it means in simple terms.
        </p>
      </div>

      {/* Example cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
        {EXAMPLE_QUERIES.map(eq => (
          <button
            key={eq.label}
            onClick={() => onSelect({ query: eq.query, ticker: eq.ticker, as_of: eq.as_of })}
            className="group text-left glass-panel p-4 hover:border-accent/30 hover:shadow-glow-accent transition-all"
          >
            <div className="min-w-0">
              <div className="text-sm font-semibold text-text-secondary group-hover:text-accent-glow transition-colors mb-1">
                {eq.chipLabel}
              </div>
              <div className="text-xs text-text-muted leading-relaxed line-clamp-2">{eq.query}</div>
            </div>
          </button>
        ))}
      </div>

      {/* How it works */}
      <div className="mt-10 flex items-center gap-6 text-xs text-text-muted">
        {[
          '10 data sources analysed',
          'Evidence-weighted scoring',
          'AI-written research note',
        ].map(text => (
          <div key={text} className="flex items-center gap-1.5">
            <span className="w-1 h-1 rounded-full bg-border" />
            <span>{text}</span>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
