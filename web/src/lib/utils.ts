import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { SignalLabel } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(
  value: number | string | null | undefined,
  opts: { decimals?: number; prefix?: string; suffix?: string } = {}
): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  const { decimals = 2, prefix = '', suffix = '' } = opts
  return `${prefix}${value.toFixed(decimals)}${suffix}`
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return '—'
  return `${value > 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

export function signalColors(label: SignalLabel) {
  switch (label) {
    case 'tailwind':
      return {
        text: 'text-tailwind',
        bg: 'bg-tailwind-dim',
        border: 'border-tailwind/20',
        glow: 'card-done-tailwind',
        badge: 'signal-tailwind',
        dot: 'bg-tailwind',
        hex: '#10b981',
      }
    case 'headwind':
      return {
        text: 'text-headwind',
        bg: 'bg-headwind-dim',
        border: 'border-headwind/20',
        glow: 'card-done-headwind',
        badge: 'signal-headwind',
        dot: 'bg-headwind',
        hex: '#ef4444',
      }
    default:
      return {
        text: 'text-neutral',
        bg: 'bg-neutral-dim',
        border: 'border-neutral/20',
        glow: 'card-done-neutral',
        badge: 'signal-neutral',
        dot: 'bg-neutral',
        hex: '#6b7280',
      }
  }
}

export function signalIcon(label: SignalLabel): string {
  switch (label) {
    case 'tailwind': return '↑'
    case 'headwind': return '↓'
    default: return '→'
  }
}

export function qualityLabel(q: number): string {
  if (q >= 0.9) return 'High'
  if (q >= 0.7) return 'Medium'
  if (q >= 0.5) return 'Low'
  return 'Very Low'
}

export function latencyLabel(ms: number): string {
  if (ms < 500) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

/** Format an ISO date string to a short display format, e.g. "Dec 2, 2024" */
export function formatDate(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

/** Clamp a value to [min, max] */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

/** Map a signal in [-1, 1] to a 0-100 percentage for display */
export function signalToPercent(s: number): number {
  return Math.round(((clamp(s, -1, 1) + 1) / 2) * 100)
}
