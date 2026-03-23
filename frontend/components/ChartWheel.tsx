'use client'

import { motion } from 'framer-motion'

interface Position {
  sign: string
  deg: number
}

interface Props {
  positions: Record<string, Position>
  houses?: Array<{ sign: string; deg: number }>
}

const SIGN_OFFSETS: Record<string, number> = {
  Aries: 0,
  Taurus: 30,
  Gemini: 60,
  Cancer: 90,
  Leo: 120,
  Virgo: 150,
  Libra: 180,
  Scorpio: 210,
  Sagittarius: 240,
  Capricorn: 270,
  Aquarius: 300,
  Pisces: 330,
}

const SIGN_SYMBOLS: Record<string, string> = {
  Aries: '\u2648',
  Taurus: '\u2649',
  Gemini: '\u264A',
  Cancer: '\u264B',
  Leo: '\u264C',
  Virgo: '\u264D',
  Libra: '\u264E',
  Scorpio: '\u264F',
  Sagittarius: '\u2650',
  Capricorn: '\u2651',
  Aquarius: '\u2652',
  Pisces: '\u2653',
}

const PLANET_SYMBOLS: Record<string, string> = {
  sun: '\u2609',
  moon: '\u263D',
  mercury: '\u263F',
  venus: '\u2640',
  mars: '\u2642',
  jupiter: '\u2643',
  saturn: '\u2644',
  uranus: '\u26E2',
  neptune: '\u2646',
  pluto: '\u2647',
}

function toAbsoluteDeg(sign: string, deg: number): number {
  return (SIGN_OFFSETS[sign] || 0) + deg
}

function polarToXY(cx: number, cy: number, r: number, degAngle: number) {
  const rad = ((degAngle - 90) * Math.PI) / 180
  return {
    x: cx + r * Math.cos(rad),
    y: cy + r * Math.sin(rad),
  }
}

export default function ChartWheel({ positions, houses }: Props) {
  const cx = 250
  const cy = 250
  const outerR = 230
  const signR = 200
  const innerR = 170
  const planetR = 140
  const centerR = 60

  // Ascendant offset so AC is on the left (180 deg)
  const ascDeg = positions.ascendant
    ? toAbsoluteDeg(positions.ascendant.sign, positions.ascendant.deg)
    : 0
  const offset = 180 - ascDeg

  function adjustDeg(sign: string, deg: number) {
    return (toAbsoluteDeg(sign, deg) + offset + 360) % 360
  }

  return (
    <motion.div
      className="relative"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
    >
      {/* Glow effect */}
      <div className="absolute inset-0 rounded-full bg-violet/10 blur-[60px] -z-10" />

      <svg viewBox="0 0 500 500" className="w-full max-w-lg mx-auto">
        {/* Outer ring */}
        <circle cx={cx} cy={cy} r={outerR} fill="none" stroke="rgba(201,169,110,0.25)" strokeWidth="1.5" />
        <circle cx={cx} cy={cy} r={signR} fill="none" stroke="rgba(201,169,110,0.15)" strokeWidth="0.5" />
        <circle cx={cx} cy={cy} r={innerR} fill="none" stroke="rgba(201,169,110,0.2)" strokeWidth="1" />
        <circle cx={cx} cy={cy} r={centerR} fill="none" stroke="rgba(123,94,167,0.2)" strokeWidth="0.5" />

        {/* Sign divisions and symbols */}
        {Object.entries(SIGN_SYMBOLS).map(([sign, symbol]) => {
          const baseDeg = (SIGN_OFFSETS[sign] + offset + 360) % 360
          const midDeg = baseDeg + 15

          // Division line
          const p1 = polarToXY(cx, cy, innerR, baseDeg)
          const p2 = polarToXY(cx, cy, outerR, baseDeg)

          // Symbol position
          const sp = polarToXY(cx, cy, (signR + outerR) / 2, midDeg)

          return (
            <g key={sign}>
              <line
                x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke="rgba(201,169,110,0.12)" strokeWidth="0.5"
              />
              <text
                x={sp.x} y={sp.y}
                textAnchor="middle" dominantBaseline="central"
                fill="rgba(201,169,110,0.5)" fontSize="14"
              >
                {symbol}
              </text>
            </g>
          )
        })}

        {/* House cusps */}
        {houses?.map((house, i) => {
          const deg = adjustDeg(house.sign, house.deg)
          const p1 = polarToXY(cx, cy, centerR, deg)
          const p2 = polarToXY(cx, cy, innerR, deg)
          const lp = polarToXY(cx, cy, centerR + 12, deg)

          return (
            <g key={`house-${i}`}>
              <line
                x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke="rgba(123,94,167,0.25)" strokeWidth="0.5"
                strokeDasharray={i % 3 === 0 ? 'none' : '2,2'}
              />
              <text
                x={lp.x} y={lp.y}
                textAnchor="middle" dominantBaseline="central"
                fill="rgba(139,138,155,0.4)" fontSize="8"
              >
                {i + 1}
              </text>
            </g>
          )
        })}

        {/* Planets */}
        {Object.entries(PLANET_SYMBOLS).map(([key, symbol]) => {
          const pos = positions[key]
          if (!pos) return null

          const deg = adjustDeg(pos.sign, pos.deg)
          const p = polarToXY(cx, cy, planetR, deg)
          const isGold = ['sun', 'venus', 'jupiter'].includes(key)

          return (
            <g key={key}>
              <circle
                cx={p.x} cy={p.y} r={12}
                fill="rgba(10,10,15,0.8)"
                stroke={isGold ? 'rgba(201,169,110,0.3)' : 'rgba(123,94,167,0.3)'}
                strokeWidth="0.5"
              />
              <text
                x={p.x} y={p.y}
                textAnchor="middle" dominantBaseline="central"
                fill={isGold ? '#C9A96E' : '#7B5EA7'}
                fontSize="13"
              >
                {symbol}
              </text>
            </g>
          )
        })}

        {/* Ascendant arrow */}
        {positions.ascendant && (
          <g>
            <text
              x={cx - outerR - 8} y={cy + 4}
              textAnchor="end" fill="#C9A96E" fontSize="11" fontWeight="600"
            >
              AC
            </text>
          </g>
        )}

        {/* MC label */}
        {positions.midheaven && (() => {
          const mcDeg = adjustDeg(positions.midheaven.sign, positions.midheaven.deg)
          const mcp = polarToXY(cx, cy, outerR + 14, mcDeg)
          return (
            <text
              x={mcp.x} y={mcp.y}
              textAnchor="middle" fill="#C9A96E" fontSize="11" fontWeight="600"
            >
              MC
            </text>
          )
        })()}
      </svg>
    </motion.div>
  )
}
