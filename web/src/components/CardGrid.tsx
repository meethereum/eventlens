import { motion } from 'framer-motion'
import AnalysisCard from './AnalysisCard'
import LockedCard from './LockedCard'
import type { CardOutput } from '@/types'
import { cardDisplayName } from '@/lib/companies'

interface Props {
  cards: CardOutput[]
  onCardClick: (card: CardOutput) => void
}

const CARD_IDS = ['C1','C2','C3','C4','C5','C6','C7','C8','C9','C10']

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
}
const item = {
  hidden: { opacity: 0, y: 16, scale: 0.98 },
  show:   { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3, ease: 'easeOut' } },
}

export default function CardGrid({ cards, onCardClick }: Props) {
  const cardMap = Object.fromEntries(cards.map(c => [c.id, c]))

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
    >
      {CARD_IDS.map(id => {
        const card = cardMap[id]
        return (
          <motion.div key={id} variants={item}>
            {card ? (
              <AnalysisCard
                card={card}
                onClick={() => onCardClick(card)}
              />
            ) : (
              <AnalysisCard
                card={{
                  id,
                  title: cardDisplayName(id),
                  status: 'queued',
                  as_of: '', fetched_at: '', latency_ms: 0,
                  headline: null, metrics: [], series: [],
                  signal: 0, label: 'neutral', weight: 0.6, quality: 1,
                  reasoning: [], math: null, sources: [], warnings: [],
                }}
                onClick={() => {}}
                disabled
              />
            )}
          </motion.div>
        )
      })}

      {/* C11 — locked */}
      <motion.div variants={item}>
        <LockedCard />
      </motion.div>
    </motion.div>
  )
}
