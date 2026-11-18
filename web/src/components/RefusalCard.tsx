import { motion } from 'framer-motion'
import { AlertCircle, ArrowRight } from 'lucide-react'
import { EXAMPLE_QUERIES } from '@/lib/mockData'
import type { SubmitPayload } from '@/components/QueryBar'

interface Props {
  message: string
  onSelectExample: (payload: SubmitPayload) => void
}

export default function RefusalCard({ message, onSelectExample }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="glass-panel p-6 border-amber/15 max-w-2xl mx-auto"
    >
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-amber-muted border border-amber/20 flex items-center justify-center shrink-0">
          <AlertCircle className="w-5 h-5 text-amber" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-text-primary mb-2">
            EventLens doesn't answer that
          </h3>
          <p className="text-sm text-text-secondary leading-relaxed mb-5">
            {message}
          </p>

          <div className="border-t border-border pt-4">
            <p className="text-xs text-text-muted mb-3 font-medium">Instead, try asking:</p>
            <div className="space-y-2">
              {EXAMPLE_QUERIES.map(eq => (
                <button
                  key={eq.label}
                  onClick={() => onSelectExample({ query: eq.query, ticker: eq.ticker, as_of: eq.as_of })}
                  className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm border border-border bg-surface-3 text-text-secondary hover:border-accent/30 hover:text-accent-glow hover:bg-accent-muted transition-all group"
                >
                  <span className="text-lg">{eq.emoji}</span>
                  <span className="flex-1">{eq.query}</span>
                  <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
