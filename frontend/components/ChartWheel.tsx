'use client'

import { motion } from 'framer-motion'

interface Position {
  sign: string
  deg: number
}

interface Aspect {
  p1: string
  p2: string
  aspect: string
  orbit: number
}

interface Props {
  positions: Record<string, Position>
  houses?: Array<{ sign: string; deg: number }>
  aspects?: Aspect[]
  birthName?: string
  birthDate?: string
  birthTime?: string
  birthCity?: string
}

// Kerykeion returns abbreviated sign names — map all variants to full names
const SIGN_NORMALIZE: Record<string, string> = {
  Ari: 'Aries', Aries: 'Aries',
  Tau: 'Taurus', Taurus: 'Taurus',
  Gem: 'Gemini', Gemini: 'Gemini',
  Can: 'Cancer', Cancer: 'Cancer',
  Leo: 'Leo',
  Vir: 'Virgo', Virgo: 'Virgo',
  Lib: 'Libra', Libra: 'Libra',
  Sco: 'Scorpio', Scorpio: 'Scorpio',
  Sag: 'Sagittarius', Sagittarius: 'Sagittarius',
  Cap: 'Capricorn', Capricorn: 'Capricorn',
  Aqu: 'Aquarius', Aquarius: 'Aquarius',
  Pis: 'Pisces', Pisces: 'Pisces',
}

function normSign(sign: string): string {
  return SIGN_NORMALIZE[sign] || sign
}

const SIGN_ORDER = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

const SIGN_OFFSETS: Record<string, number> = {}
SIGN_ORDER.forEach((s, i) => { SIGN_OFFSETS[s] = i * 30 })

const SIGN_SYMBOLS: Record<string, string> = {
  Aries: '\u2648', Taurus: '\u2649', Gemini: '\u264A', Cancer: '\u264B',
  Leo: '\u264C', Virgo: '\u264D', Libra: '\u264E', Scorpio: '\u264F',
  Sagittarius: '\u2650', Capricorn: '\u2651', Aquarius: '\u2652', Pisces: '\u2653',
}

const PLANET_SYMBOLS: Record<string, string> = {
  sun: '\u2609', moon: '\u263D', mercury: '\u263F', venus: '\u2640',
  mars: '\u2642', jupiter: '\u2643', saturn: '\u2644', uranus: '\u26E2',
  neptune: '\u2646', pluto: '\u2647',
}

// Normalize planet name from kerykeion (e.g., "Sun" -> "sun")
const PLANET_NAME_MAP: Record<string, string> = {
  Sun: 'sun', Moon: 'moon', Mercury: 'mercury', Venus: 'venus',
  Mars: 'mars', Jupiter: 'jupiter', Saturn: 'saturn', Uranus: 'uranus',
  Neptune: 'neptune', Pluto: 'pluto',
  sun: 'sun', moon: 'moon', mercury: 'mercury', venus: 'venus',
  mars: 'mars', jupiter: 'jupiter', saturn: 'saturn', uranus: 'uranus',
  neptune: 'neptune', pluto: 'pluto',
}

// Aspect colors and styles
const ASPECT_STYLES: Record<string, { color: string; dash?: string; opacity: number; width: number }> = {
  conjunction: { color: '#FFD700', opacity: 1, width: 1.5 },
  opposition: { color: '#FF4444', dash: '6,3', opacity: 0.9, width: 1.3 },
  trine: { color: '#44FF88', opacity: 0.85, width: 1.2 },
  square: { color: '#FF6644', opacity: 0.85, width: 1.2 },
  sextile: { color: '#44AAFF', dash: '5,3', opacity: 0.8, width: 1 },
  quincunx: { color: '#BB77FF', dash: '3,4', opacity: 0.7, width: 0.8 },
  semisextile: { color: '#BB77FF', dash: '2,4', opacity: 0.6, width: 0.7 },
}

function toAbsoluteDeg(sign: string, deg: number): number {
  const norm = normSign(sign)
  return (SIGN_OFFSETS[norm] ?? 0) + deg
}

function polarToXY(cx: number, cy: number, r: number, degAngle: number) {
  // Astrological chart: counter-clockwise, AC at left (180°)
  // degAngle is the adjusted zodiac degree (AC = 180°)
  // Convert to standard math angle and negate Y for SVG coordinate system
  const rad = (degAngle * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy - r * Math.sin(rad) }
}

// Spread planets that are too close to each other
function spreadPlanets(items: { key: string; deg: number }[], minGap: number) {
  const sorted = [...items].sort((a, b) => a.deg - b.deg)
  for (let pass = 0; pass < 5; pass++) {
    for (let i = 0; i < sorted.length; i++) {
      const next = sorted[(i + 1) % sorted.length]
      const curr = sorted[i]
      const diff = ((next.deg - curr.deg) + 360) % 360
      if (diff < minGap && diff > 0) {
        const nudge = (minGap - diff) / 2
        curr.deg = (curr.deg - nudge + 360) % 360
        next.deg = (next.deg + nudge) % 360
      }
    }
  }
  return sorted
}

export default function ChartWheel({ positions, houses, aspects, birthName, birthDate, birthTime, birthCity }: Props) {
  const cx = 300
  const cy = 300
  const outerR = 275
  const signBandR = 245
  const innerR = 215
  const planetR = 175
  const houseNumR = 135
  const aspectR = 155 // radius for aspect lines (closer to planets for better visual)
  const centerR = 55

  // Ascendant offset so AC is on the left (180 deg)
  const ascDeg = positions.ascendant
    ? toAbsoluteDeg(positions.ascendant.sign, positions.ascendant.deg)
    : 0
  const offset = 180 - ascDeg

  function adj(sign: string, deg: number) {
    return (toAbsoluteDeg(sign, deg) + offset + 360) % 360
  }

  // Prepare planets with spread
  const planetEntries = Object.entries(PLANET_SYMBOLS)
    .map(([key, symbol]) => {
      const pos = positions[key]
      if (!pos) return null
      return { key, symbol, deg: adj(pos.sign, pos.deg), realDeg: adj(pos.sign, pos.deg) }
    })
    .filter(Boolean) as { key: string; symbol: string; deg: number; realDeg: number }[]

  const spread = spreadPlanets(
    planetEntries.map(p => ({ key: p.key, deg: p.deg })),
    10
  )
  const planetMap = new Map(spread.map(s => [s.key, s.deg]))

  // Build a map of planet real positions (before spread) for aspect lines
  const planetRealDegMap = new Map<string, number>()
  planetEntries.forEach(p => {
    planetRealDegMap.set(p.key, p.realDeg)
  })

  return (
    <motion.div
      className="relative"
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
    >
      {/* Glow */}
      <div className="absolute inset-0 rounded-full bg-violet/10 blur-[80px] -z-10" />

      <svg viewBox="0 0 600 680" className="chart-wheel-svg w-full max-w-xl mx-auto drop-shadow-2xl">
        <defs>
          <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(18,18,26,0.95)" />
            <stop offset="100%" stopColor="rgba(10,10,15,0.98)" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background circle */}
        <circle cx={cx} cy={cy} r={outerR + 10} fill="url(#bgGrad)" />

        {/* Rings */}
        <circle cx={cx} cy={cy} r={outerR} fill="none" stroke="rgba(201,169,110,0.4)" strokeWidth="1.5" />
        <circle cx={cx} cy={cy} r={signBandR} fill="none" stroke="rgba(201,169,110,0.15)" strokeWidth="0.5" />
        <circle cx={cx} cy={cy} r={innerR} fill="none" stroke="rgba(201,169,110,0.35)" strokeWidth="1.2" />
        <circle cx={cx} cy={cy} r={centerR} fill="none" stroke="rgba(123,94,167,0.25)" strokeWidth="0.7" />

        {/* Sign divisions and symbols */}
        {SIGN_ORDER.map((sign) => {
          const baseDeg = (SIGN_OFFSETS[sign] + offset + 360) % 360
          const midDeg = baseDeg + 15
          const symbol = SIGN_SYMBOLS[sign]

          const p1 = polarToXY(cx, cy, innerR, baseDeg)
          const p2 = polarToXY(cx, cy, outerR, baseDeg)
          const sp = polarToXY(cx, cy, (signBandR + outerR) / 2, midDeg)

          return (
            <g key={sign}>
              <line
                x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke="rgba(201,169,110,0.25)" strokeWidth="0.7"
              />
              <text
                x={sp.x} y={sp.y}
                textAnchor="middle" dominantBaseline="central"
                fill="rgba(201,169,110,0.6)" fontSize="15"
                fontFamily="serif"
              >
                {symbol}
              </text>
            </g>
          )
        })}

        {/* House cusps */}
        {houses?.map((house, i) => {
          const deg = adj(house.sign, house.deg)
          const isCardinal = i === 0 || i === 3 || i === 6 || i === 9
          const p1 = polarToXY(cx, cy, centerR, deg)
          const p2 = polarToXY(cx, cy, innerR, deg)
          const lp = polarToXY(cx, cy, houseNumR, deg + (i === 0 || i === 9 ? -6 : 6))

          return (
            <g key={`house-${i}`}>
              <line
                x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke={isCardinal ? 'rgba(201,169,110,0.6)' : 'rgba(139,138,155,0.35)'}
                strokeWidth={isCardinal ? '1.5' : '0.7'}
                strokeDasharray={isCardinal ? 'none' : '4,4'}
              />
              <text
                x={lp.x} y={lp.y}
                textAnchor="middle" dominantBaseline="central"
                fill="rgba(201,169,110,0.5)" fontSize="11" fontWeight="500"
              >
                {i + 1}
              </text>
            </g>
          )
        })}

        {/* ── Aspect Lines ─────────────────────────────── */}
        {aspects && aspects.length > 0 && aspects.map((aspect, i) => {
          const p1Key = PLANET_NAME_MAP[aspect.p1] || aspect.p1.toLowerCase()
          const p2Key = PLANET_NAME_MAP[aspect.p2] || aspect.p2.toLowerCase()

          const deg1 = planetRealDegMap.get(p1Key)
          const deg2 = planetRealDegMap.get(p2Key)

          if (deg1 === undefined || deg2 === undefined) return null

          const pos1 = polarToXY(cx, cy, aspectR, deg1)
          const pos2 = polarToXY(cx, cy, aspectR, deg2)

          const aspectName = aspect.aspect?.toLowerCase() || ''
          const style = ASPECT_STYLES[aspectName] || { color: '#8B8A9B', opacity: 0.4, width: 0.8 }

          return (
            <line
              key={`aspect-${i}`}
              x1={pos1.x} y1={pos1.y}
              x2={pos2.x} y2={pos2.y}
              stroke={style.color}
              strokeWidth={String(style.width)}
              strokeDasharray={style.dash || 'none'}
              opacity={style.opacity}
            />
          )
        })}

        {/* Planets */}
        {planetEntries.map(({ key, symbol }) => {
          const deg = planetMap.get(key) ?? 0
          const p = polarToXY(cx, cy, planetR, deg)
          const isLuminary = key === 'sun' || key === 'moon'
          const isGold = ['sun', 'venus', 'jupiter'].includes(key)
          const color = isGold ? '#C9A96E' : '#7B5EA7'
          const r = isLuminary ? 15 : 12

          return (
            <g key={key} filter={isLuminary ? 'url(#glow)' : undefined}>
              <circle
                cx={p.x} cy={p.y} r={r}
                fill="rgba(10,10,15,0.9)"
                stroke={color}
                strokeWidth="1"
                opacity="0.9"
              />
              <text
                x={p.x} y={p.y}
                textAnchor="middle" dominantBaseline="central"
                fill={color}
                fontSize={isLuminary ? '15' : '12'}
                fontWeight={isLuminary ? '600' : '400'}
              >
                {symbol}
              </text>
            </g>
          )
        })}

        {/* AC label */}
        {positions.ascendant && (
          <text
            x={cx - outerR - 15} y={cy + 4}
            textAnchor="end" fill="#C9A96E" fontSize="12" fontWeight="700"
            letterSpacing="1"
          >
            AC
          </text>
        )}

        {/* MC-IC axis line */}
        {positions.midheaven && (() => {
          const mcDeg = adj(positions.midheaven.sign, positions.midheaven.deg)
          const icDeg = (mcDeg + 180) % 360
          const mc1 = polarToXY(cx, cy, centerR, mcDeg)
          const mc2 = polarToXY(cx, cy, innerR, mcDeg)
          const ic1 = polarToXY(cx, cy, centerR, icDeg)
          const ic2 = polarToXY(cx, cy, innerR, icDeg)
          const mcp = polarToXY(cx, cy, outerR + 20, mcDeg)
          const icp = polarToXY(cx, cy, outerR + 20, icDeg)
          return (
            <g>
              {/* MC axis line */}
              <line x1={mc1.x} y1={mc1.y} x2={mc2.x} y2={mc2.y}
                stroke="#C9A96E" strokeWidth="1.5" strokeDasharray="4,3" opacity="0.6" />
              {/* IC axis line */}
              <line x1={ic1.x} y1={ic1.y} x2={ic2.x} y2={ic2.y}
                stroke="rgba(201,169,110,0.3)" strokeWidth="1" strokeDasharray="4,3" />
              {/* MC label - prominent */}
              <text x={mcp.x} y={mcp.y} textAnchor="middle" dominantBaseline="central"
                fill="#C9A96E" fontSize="14" fontWeight="700" letterSpacing="1">
                MC
              </text>
              {/* IC label */}
              <text x={icp.x} y={icp.y} textAnchor="middle" dominantBaseline="central"
                fill="rgba(201,169,110,0.4)" fontSize="10" fontWeight="600" letterSpacing="1">
                IC
              </text>
            </g>
          )
        })()}

        {/* DC label (opposite of AC) */}
        <text
          x={cx + outerR + 15} y={cy + 4}
          textAnchor="start" fill="rgba(201,169,110,0.4)" fontSize="10" fontWeight="600"
          letterSpacing="1"
        >
          DC
        </text>

        {/* IC label already rendered in MC-IC axis group above */}

        {/* ── Birth Info ─────────────────────────────── */}
        {birthName && (
          <text x={cx} y={610} textAnchor="middle" fill="#C9A96E" fontSize="14" fontWeight="600" fontFamily="serif">
            {birthName}
          </text>
        )}
        {(birthDate || birthTime || birthCity) && (
          <text x={cx} y={632} textAnchor="middle" fill="#8B8A9B" fontSize="11">
            {[birthDate, birthTime, birthCity].filter(Boolean).join(' · ')}
          </text>
        )}
        <text x={cx} y={655} textAnchor="middle" fill="rgba(201,169,110,0.3)" fontSize="9" fontFamily="sans-serif">
          astrara.online
        </text>
      </svg>
    </motion.div>
  )
}
