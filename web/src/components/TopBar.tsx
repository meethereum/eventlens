import type { HealthResponse } from '@/types'

interface Props {
  health: HealthResponse
}

export default function TopBar({ health }: Props) {
  return (
    <header className="sticky top-0 z-30 w-full border-b border-border/50 bg-surface-1/95 backdrop-blur-md">
      <div className="max-w-screen-xl mx-auto px-4 md:px-6 h-14 flex items-center justify-between">

        {/* Logo */}
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="relative w-8 h-8">
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-accent to-accent-dim opacity-90" />
            <div className="absolute inset-0 rounded-xl flex items-center justify-center">
              <svg viewBox="0 0 20 20" className="w-4 h-4 text-white" fill="none">
                <circle cx="8.5" cy="8.5" r="5" stroke="currentColor" strokeWidth="1.8" />
                <line x1="12.5" y1="12.5" x2="17" y2="17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                <rect x="6" y="10" width="1.5" height="2.5" rx="0.5" fill="currentColor" opacity="0.7" />
                <rect x="8.2" y="8.5" width="1.5" height="4" rx="0.5" fill="currentColor" opacity="0.85" />
              </svg>
            </div>
          </div>
          <div className="flex items-baseline">
            <span
              className="text-lg font-semibold text-text-primary"
              style={{ letterSpacing: '-0.02em' }}
            >
              Event
            </span>
            <span
              className="text-lg font-semibold text-accent-glow"
              style={{ letterSpacing: '-0.02em' }}
            >
              Lens
            </span>
          </div>
        </div>

        {/* Right side */}
        {health.demo_mode && (
          <span className="text-xs font-medium text-amber border border-amber/20 bg-amber-muted px-2.5 py-1 rounded-full">
            Demo
          </span>
        )}
      </div>
    </header>
  )
}
