import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      // ----------------------------------------------------------------
      // EventLens design tokens
      // ----------------------------------------------------------------
      colors: {
        // Near-black backgrounds
        surface: {
          DEFAULT: '#0a0c0f',
          1: '#0f1218',
          2: '#141820',
          3: '#1a2030',
          4: '#1e2535',
        },
        // 1px panel borders
        border: {
          DEFAULT: '#1f2937',
          subtle: '#151c26',
          bright: '#2d3748',
        },
        // Electric accent (cyan-blue)
        accent: {
          DEFAULT: '#3b82f6',   // blue-500
          dim: '#1d4ed8',
          glow: '#60a5fa',
          muted: '#1e3a5f',
        },
        // Amber warnings
        amber: {
          DEFAULT: '#f59e0b',
          dim: '#92400e',
          glow: '#fbbf24',
          muted: '#451a03',
        },
        // Signal colours
        tailwind: {
          DEFAULT: '#10b981',   // emerald-500
          dim: '#065f46',
          glow: '#34d399',
        },
        headwind: {
          DEFAULT: '#ef4444',   // red-500
          dim: '#7f1d1d',
          glow: '#f87171',
        },
        neutral: {
          DEFAULT: '#6b7280',   // gray-500
          dim: '#374151',
        },
        // Text
        text: {
          primary: '#f1f5f9',
          secondary: '#94a3b8',
          muted: '#475569',
          dim: '#334155',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.65rem', { lineHeight: '1rem' }],
      },
      boxShadow: {
        'glow-accent': '0 0 20px rgba(59,130,246,0.15)',
        'glow-tailwind': '0 0 20px rgba(16,185,129,0.15)',
        'glow-headwind': '0 0 20px rgba(239,68,68,0.15)',
        'glow-amber': '0 0 20px rgba(245,158,11,0.15)',
        'glass': 'inset 0 1px 0 rgba(255,255,255,0.04)',
      },
      backgroundImage: {
        'grid-pattern': `linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                         linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)`,
      },
      backgroundSize: {
        'grid': '32px 32px',
      },
      animation: {
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-soft': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'count-up': 'count-up 0.6s ease-out forwards',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config
