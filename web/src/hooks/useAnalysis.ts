/**
 * useAnalysis — connects to POST /api/analyze SSE stream and drives
 * the full AnalysisState from raw SSE events.
 *
 * Returns { state, run, reset }.
 */
import { useCallback, useRef, useState } from 'react'
import type {
  AnalysisState,
  CardOutput,
  ParsedQuery,
  AggregateResult,
  VerdictOutput,
} from '@/types'

// ---------------------------------------------------------------------------
// Initial state factory
// ---------------------------------------------------------------------------
function emptyState(): AnalysisState {
  return {
    runId: null,
    query: '',
    parsed: null,
    cards: {},
    aggregate: null,
    verdict: null,
    verdictStream: '',
    phase: 'idle',
    pipelineTimings: {},
    error: null,
  }
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>(emptyState())
  const abortRef = useRef<AbortController | null>(null)
  const phaseStartRef = useRef<number>(Date.now())

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(emptyState())
  }, [])

  const run = useCallback(async (query: string, ticker = '', asOf = '') => {
    // Cancel any in-flight request
    abortRef.current?.abort()
    const abort = new AbortController()
    abortRef.current = abort

    phaseStartRef.current = Date.now()

    setState({
      ...emptyState(),
      query,
      phase: 'parsing',
    })

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, ticker, as_of: asOf }),
        signal: abort.signal,
      })

      if (!res.ok || !res.body) {
        const text = await res.text().catch(() => 'unknown error')
        setState(s => ({ ...s, phase: 'error', error: `HTTP ${res.status}: ${text}` }))
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      for (;;) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // SSE frames are separated by \n\n
        const frames = buffer.split('\n\n')
        buffer = frames.pop() ?? ''   // last (possibly incomplete) frame

        for (const frame of frames) {
          const dataLine = frame
            .split('\n')
            .find(l => l.startsWith('data:'))
          if (!dataLine) continue

          const json = dataLine.slice('data:'.length).trim()
          if (!json) continue

          let event: { type: string; run_id: string; data: unknown }
          try {
            event = JSON.parse(json)
          } catch {
            continue
          }

          handleEvent(event.type, event.run_id, event.data, setState, phaseStartRef)
        }
      }
    } catch (err: unknown) {
      if ((err as Error)?.name === 'AbortError') return
      setState(s => ({
        ...s,
        phase: 'error',
        error: (err as Error)?.message ?? 'Stream error',
      }))
    }
  }, [])

  return { state, run, reset }
}

// ---------------------------------------------------------------------------
// Event dispatcher
// ---------------------------------------------------------------------------
function handleEvent(
  type: string,
  runId: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any,
  setState: React.Dispatch<React.SetStateAction<AnalysisState>>,
  phaseStartRef: React.MutableRefObject<number>,
) {
  const elapsed = () => Date.now() - phaseStartRef.current

  switch (type) {
    case 'query_parsed': {
      const parsed = data?.parsed as ParsedQuery
      setState(s => ({
        ...s,
        runId,
        parsed,
        phase: 'scope_check',
        pipelineTimings: { ...s.pipelineTimings, parsing: elapsed() },
      }))
      phaseStartRef.current = Date.now()
      break
    }

    case 'scope_check': {
      const inScope: boolean = data?.in_scope ?? true
      setState(s => ({
        ...s,
        pipelineTimings: { ...s.pipelineTimings, scope_check: elapsed() },
        // If out of scope, store refusal in a special card-like slot
        ...(inScope
          ? { phase: 'fetching' }
          : {
              phase: 'done',
              cards: {
                ...s.cards,
                _refusal: {
                  id: '_refusal',
                  title: 'Out of scope',
                  status: 'error',
                  as_of: '',
                  fetched_at: '',
                  latency_ms: 0,
                  headline: null,
                  metrics: [],
                  series: [],
                  signal: 0,
                  label: 'neutral',
                  weight: 0,
                  quality: 0,
                  reasoning: [],
                  math: null,
                  sources: [],
                  warnings: [],
                  error_message: data?.refusal_message ?? 'Query out of scope.',
                } as CardOutput,
              },
            }),
      }))
      phaseStartRef.current = Date.now()
      break
    }

    case 'card_start': {
      const cardId: string = data?.card_id
      const title: string = data?.title ?? cardId
      setState(s => ({
        ...s,
        cards: {
          ...s.cards,
          [cardId]: s.cards[cardId]
            ? { ...s.cards[cardId], status: 'fetching' }
            : {
                id: cardId,
                title,
                status: 'fetching',
                as_of: '',
                fetched_at: '',
                latency_ms: 0,
                headline: null,
                metrics: [],
                series: [],
                signal: 0,
                label: 'neutral',
                weight: 0.6,
                quality: 1,
                reasoning: [],
                math: null,
                sources: [],
                warnings: [],
              } as CardOutput,
        },
      }))
      break
    }

    case 'card_done': {
      const card = data?.card as CardOutput
      if (!card) break
      setState(s => ({
        ...s,
        cards: { ...s.cards, [card.id]: { ...card, status: 'done' } },
      }))
      break
    }

    case 'card_error': {
      const cardId: string = data?.card_id
      const errMsg: string = data?.error ?? 'Failed to fetch'
      setState(s => ({
        ...s,
        cards: {
          ...s.cards,
          [cardId]: {
            ...(s.cards[cardId] ?? { id: cardId, title: cardId }),
            status: 'error',
            error_message: errMsg,
          } as CardOutput,
        },
      }))
      break
    }

    case 'aggregate': {
      const agg = data?.result as AggregateResult
      setState(s => ({
        ...s,
        aggregate: agg,
        phase: 'synthesising',
        pipelineTimings: { ...s.pipelineTimings, fetching: elapsed(), scoring: 0 },
      }))
      phaseStartRef.current = Date.now()
      break
    }

    case 'verdict_delta': {
      const delta: string = data?.delta ?? ''
      setState(s => ({
        ...s,
        verdictStream: s.verdictStream + delta,
      }))
      break
    }

    case 'verdict_done': {
      const verdict = data?.verdict as VerdictOutput
      setState(s => ({
        ...s,
        verdict,
        verdictStream: '',
        pipelineTimings: { ...s.pipelineTimings, synthesising: elapsed() },
      }))
      phaseStartRef.current = Date.now()
      break
    }

    case 'done': {
      setState(s => ({
        ...s,
        phase: 'done',
        // The SSE envelope is authoritative. This also prevents a recorded
        // fixture's historical payload ID from replacing the active run ID.
        runId: runId || s.runId,
      }))
      break
    }

    case 'error': {
      setState(s => ({
        ...s,
        phase: 'error',
        error: (data?.message as string) ?? 'Unknown error from server',
      }))
      break
    }
  }
}
