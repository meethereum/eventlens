import { Lock } from 'lucide-react'

export default function LockedCard() {
  return (
    <div
      className="glass-panel p-5 relative overflow-hidden opacity-40 select-none"
      style={{
        backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.01) 10px, rgba(255,255,255,0.01) 20px)',
      }}
    >
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-text-primary">Historical Precedents</h3>
        <p className="text-xs text-text-muted mt-0.5">Similar past events and what happened</p>
      </div>

      <div className="space-y-2 mb-4">
        <div className="bg-surface-3 rounded h-7 w-24" />
        <div className="bg-surface-3 rounded h-3 w-full" />
        <div className="bg-surface-3 rounded h-14 mt-2" />
      </div>

      <div className="flex items-center gap-2 text-xs text-text-muted border-t border-border pt-3">
        <Lock className="w-3.5 h-3.5" />
        <span>Coming in a future update</span>
      </div>
    </div>
  )
}
