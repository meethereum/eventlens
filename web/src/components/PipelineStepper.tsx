import { Check, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AnalysisState } from '@/types'

type Phase = AnalysisState['phase']

const STEPS: { id: Phase; label: string; detail: string }[] = [
  { id: 'parsing',      label: 'Understanding your question', detail: 'Identifying the company and event' },
  { id: 'scope_check',  label: 'Checking coverage',           detail: 'Verifying we cover this company'  },
  { id: 'fetching',     label: 'Gathering data',              detail: 'Fetching from 10 sources'          },
  { id: 'scoring',      label: 'Computing signals',           detail: 'Running the evidence math'         },
  { id: 'synthesising', label: 'Writing analysis',            detail: 'AI is drafting the research note'  },
]

const PHASE_ORDER: Phase[] = ['idle','parsing','scope_check','fetching','scoring','synthesising','done','error']

function phaseIndex(p: Phase) { return PHASE_ORDER.indexOf(p) }

function stepStatus(step: { id: Phase }, phase: Phase): 'pending' | 'active' | 'done' {
  const cur = phaseIndex(phase)
  const idx = phaseIndex(step.id)
  if (cur > idx) return 'done'
  if (cur === idx) return 'active'
  return 'pending'
}

interface Props {
  phase: Phase
  timings: Record<string, number>
}

export default function PipelineStepper({ phase, timings }: Props) {
  const isDone  = phase === 'done'
  const isError = phase === 'error'

  return (
    <div className="glass-panel px-5 py-4">
      {/* Mobile: compact progress bar */}
      <div className="flex md:hidden items-center gap-3">
        <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all duration-500',
              isError ? 'bg-headwind' : 'bg-accent')}
            style={{ width: `${(phaseIndex(phase) / (PHASE_ORDER.length - 1)) * 100}%` }}
          />
        </div>
        <span className="text-xs text-text-secondary whitespace-nowrap">
          {isDone ? 'Done' : isError ? 'Error' : STEPS.find(s => s.id === phase)?.label ?? 'Running…'}
        </span>
      </div>

      {/* Desktop: step pills */}
      <div className="hidden md:flex items-center gap-1 overflow-x-auto">
        {STEPS.map((step, i) => {
          const status = stepStatus(step, phase)
          const timing = timings[step.id]
          return (
            <div key={step.id} className="flex items-center">
              <div className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-300 whitespace-nowrap',
                status === 'active' && 'bg-accent/10 border border-accent/20',
              )}>
                {/* Icon */}
                <div className={cn(
                  'w-5 h-5 rounded-full flex items-center justify-center shrink-0 transition-all',
                  status === 'done'    && 'bg-tailwind text-white',
                  status === 'active'  && 'bg-accent text-white',
                  status === 'pending' && 'bg-surface-3 border border-border',
                )}>
                  {status === 'done'   && <Check className="w-3 h-3" />}
                  {status === 'active' && <Loader2 className="w-3 h-3 animate-spin" />}
                  {status === 'pending' && <span className="w-1.5 h-1.5 rounded-full bg-border" />}
                </div>

                <div>
                  <div className={cn(
                    'text-xs font-medium',
                    status === 'done'    && 'text-tailwind',
                    status === 'active'  && 'text-accent-glow',
                    status === 'pending' && 'text-text-muted',
                  )}>
                    {step.label}
                  </div>
                  {status === 'active' && (
                    <div className="text-2xs text-text-muted">{step.detail}</div>
                  )}
                  {timing !== undefined && status === 'done' && (
                    <div className="text-2xs text-text-muted font-mono">{timing}ms</div>
                  )}
                </div>
              </div>

              {/* Connector */}
              {i < STEPS.length - 1 && (
                <div className={cn(
                  'h-px w-4 shrink-0 transition-colors',
                  phaseIndex(phase) > phaseIndex(STEPS[i].id) ? 'bg-tailwind/40' : 'bg-border',
                )} />
              )}
            </div>
          )
        })}

        {/* Final done/error */}
        {(isDone || isError) && (
          <div className="flex items-center">
            <div className="h-px w-4 shrink-0 bg-tailwind/40" />
            <div className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg',
              isDone  && 'bg-tailwind/10 border border-tailwind/20',
              isError && 'bg-headwind/10 border border-headwind/20',
            )}>
              <div className={cn(
                'w-5 h-5 rounded-full flex items-center justify-center',
                isDone  ? 'bg-tailwind text-white' : 'bg-headwind text-white',
              )}>
                <Check className="w-3 h-3" />
              </div>
              <span className={cn('text-xs font-medium', isDone ? 'text-tailwind' : 'text-headwind')}>
                {isDone ? 'Analysis complete' : 'Something went wrong'}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
