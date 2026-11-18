import { useState } from 'react'
import { X, FlaskConical } from 'lucide-react'

interface Props {
  missingKeys: string[]
}

export default function DemoBanner({ missingKeys }: Props) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null

  return (
    <div className="bg-amber-muted/80 border-b border-amber/15 px-4 py-2.5">
      <div className="max-w-screen-xl mx-auto flex items-center gap-3">
        <FlaskConical className="w-4 h-4 text-amber shrink-0" />
        <span className="text-xs text-amber flex-1">
          <strong>Demo mode — </strong>
          using example data, not live market data.
          {missingKeys.filter(k => !k.includes('placeholder')).length > 0 && (
            <span className="text-amber/80 ml-1">
              To use live data, add your API keys to <code className="font-mono bg-amber/10 px-1 rounded">.env</code>.
            </span>
          )}
        </span>
        <button
          onClick={() => setDismissed(true)}
          className="shrink-0 text-amber/60 hover:text-amber transition-colors ml-auto"
          aria-label="Dismiss"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
