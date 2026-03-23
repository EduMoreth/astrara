'use client'

import { motion } from 'framer-motion'

interface Position {
  sign: string
  deg: number
}

interface Props {
  positions: Record<string, Position>
}

const PLANET_MAP: Record<string, { icon: string; label: string }> = {
  sun:       { icon: '\u2609', label: 'Sol' },
  moon:      { icon: '\u263D', label: 'Lua' },
  mercury:   { icon: '\u263F', label: 'Mercurio' },
  venus:     { icon: '\u2640', label: 'Venus' },
  mars:      { icon: '\u2642', label: 'Marte' },
  jupiter:   { icon: '\u2643', label: 'Jupiter' },
  saturn:    { icon: '\u2644', label: 'Saturno' },
  uranus:    { icon: '\u26E2', label: 'Urano' },
  neptune:   { icon: '\u2646', label: 'Netuno' },
  pluto:     { icon: '\u2647', label: 'Plutao' },
  ascendant: { icon: 'AC', label: 'Ascendente' },
  midheaven: { icon: 'MC', label: 'Meio do Ceu' },
}

const SIGN_TRANSLATIONS: Record<string, string> = {
  Aries: 'Aries',
  Taurus: 'Touro',
  Gemini: 'Gemeos',
  Cancer: 'Cancer',
  Leo: 'Leao',
  Virgo: 'Virgem',
  Libra: 'Libra',
  Scorpio: 'Escorpiao',
  Sagittarius: 'Sagitario',
  Capricorn: 'Capricornio',
  Aquarius: 'Aquario',
  Pisces: 'Peixes',
}

function formatDegree(deg: number): string {
  const d = Math.floor(deg)
  const m = Math.round((deg - d) * 60)
  return `${d}\u00B0${m.toString().padStart(2, '0')}'`
}

export default function PlanetTable({ positions }: Props) {
  const planetKeys = Object.keys(PLANET_MAP)

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3, duration: 0.6 }}
    >
      <h2 className="font-display text-2xl font-light text-stardust mb-6">
        Suas posicoes astrologicas
      </h2>

      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gold/10">
              <th className="text-left text-xs text-muted font-normal px-5 py-3 uppercase tracking-wider">
                Planeta
              </th>
              <th className="text-left text-xs text-muted font-normal px-5 py-3 uppercase tracking-wider">
                Signo
              </th>
              <th className="text-right text-xs text-muted font-normal px-5 py-3 uppercase tracking-wider">
                Grau
              </th>
            </tr>
          </thead>
          <tbody>
            {planetKeys.map((key, i) => {
              const pos = positions[key]
              if (!pos) return null
              const planet = PLANET_MAP[key]
              const signPt = SIGN_TRANSLATIONS[pos.sign] || pos.sign

              return (
                <motion.tr
                  key={key}
                  className="border-b border-white/[0.03] hover:bg-surface-2/50 transition-colors"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + i * 0.05 }}
                >
                  <td className="px-5 py-3.5 flex items-center gap-3">
                    <span className="text-gold text-lg w-6 text-center font-mono">
                      {planet.icon}
                    </span>
                    <span className="text-stardust text-sm">{planet.label}</span>
                  </td>
                  <td className="px-5 py-3.5 text-stardust/80 text-sm">
                    {signPt}
                  </td>
                  <td className="px-5 py-3.5 text-right text-muted text-sm font-mono">
                    {formatDegree(pos.deg)}
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
