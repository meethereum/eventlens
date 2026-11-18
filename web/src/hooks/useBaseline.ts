/**
 * useBaseline — calls POST /api/baseline for the plain LLM comparison toggle.
 */
import { useState, useCallback } from 'react'

interface BaselineState {
  response: string | null
  model_used: string
  is_fallback: boolean
  error: string | null
  loading: boolean
}

export function useBaseline() {
  const [state, setState] = useState<BaselineState>({
    response: null,
    model_used: '',
    is_fallback: false,
    error: null,
    loading: false,
  })

  const run = useCallback(async (query: string) => {
    setState(s => ({ ...s, loading: true, response: null, error: null }))
    try {
      const res = await fetch('/api/baseline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()
      setState({
        response: data.response ?? null,
        model_used: data.model_used ?? '',
        is_fallback: data.is_fallback ?? false,
        error: data.error ?? null,
        loading: false,
      })
    } catch (err) {
      setState(s => ({
        ...s,
        loading: false,
        error: (err as Error).message,
      }))
    }
  }, [])

  const reset = useCallback(() => {
    setState({ response: null, model_used: '', is_fallback: false, error: null, loading: false })
  }, [])

  return { state, run, reset }
}
