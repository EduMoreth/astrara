'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'
import { getUserCharts } from '@/lib/api'
import { getUserFromToken, removeToken } from '@/lib/auth'

interface Chart {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_city: string
  positions_json: Record<string, { sign: string; deg: number }>
  svg_data: string
  created_at: string
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

export default function DashboardPage() {
  const router = useRouter()
  const [charts, setCharts] = useState<Chart[]>([])
  const [loading, setLoading] = useState(true)
  const user = getUserFromToken()

  useEffect(() => {
    if (!user) {
      router.push('/auth/login')
      return
    }

    getUserCharts()
      .then(setCharts)
      .catch(() => toast.error('Erro ao carregar seus mapas'))
      .finally(() => setLoading(false))
  }, [])

  function handleLogout() {
    removeToken()
    router.push('/')
  }

  if (!user) return null

  return (
    <main className="relative min-h-screen">
      <StarBackground />

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">
          Astrara
        </Link>

        <div className="flex items-center gap-5">
          <div className="flex items-center gap-3">
            <span className="text-stardust text-sm">{user.name}</span>
            <span className="text-xs px-2.5 py-1 rounded-full border border-gold/20 text-gold/70">
              Free
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="text-muted hover:text-stardust transition-colors text-sm"
          >
            Sair
          </button>
        </div>
      </header>

      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto">
        {/* Title bar */}
        <div className="flex items-center justify-between mb-10">
          <h1 className="font-display text-3xl font-light text-stardust">
            Meus mapas
          </h1>
          <Link href="/chart" className="btn-primary text-sm">
            + Novo mapa
          </Link>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-20">
            <motion.div
              className="w-8 h-8 border-2 border-gold/30 border-t-gold rounded-full"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            />
          </div>
        )}

        {/* Empty state */}
        {!loading && charts.length === 0 && (
          <motion.div
            className="glass-card p-16 text-center max-w-lg mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="text-6xl mb-6 opacity-30">{'\u2728'}</div>
            <h2 className="font-display text-xl text-stardust mb-3">
              Nenhum mapa salvo ainda
            </h2>
            <p className="text-muted text-sm mb-8">
              Calcule seu primeiro mapa astral e ele aparecera aqui.
            </p>
            <Link href="/chart" className="btn-primary">
              Criar meu primeiro mapa
            </Link>
          </motion.div>
        )}

        {/* Charts grid */}
        {!loading && charts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {charts.map((chart, i) => {
              const sunSign = chart.positions_json?.sun?.sign || ''
              const ascSign = chart.positions_json?.ascendant?.sign || ''

              return (
                <motion.div
                  key={chart.id}
                  className="glass-card p-6 hover:border-gold/30 transition-all cursor-pointer group"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  {/* Mini mandala placeholder */}
                  <div className="w-20 h-20 mx-auto mb-5 rounded-full border border-gold/15 flex items-center justify-center">
                    <svg viewBox="0 0 100 100" className="w-14 h-14 opacity-40">
                      <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(201,169,110,0.3)" strokeWidth="1" />
                      <circle cx="50" cy="50" r="30" fill="none" stroke="rgba(123,94,167,0.3)" strokeWidth="0.5" />
                      <circle cx="50" cy="50" r="15" fill="none" stroke="rgba(201,169,110,0.2)" strokeWidth="0.5" />
                    </svg>
                  </div>

                  <h3 className="text-stardust font-medium text-center">{chart.name}</h3>
                  <p className="text-muted text-sm text-center mt-1">{chart.birth_date}</p>

                  <div className="flex justify-center gap-4 mt-4 text-sm">
                    {sunSign && (
                      <span className="text-gold/70">
                        {'\u2609'} {SIGN_TRANSLATIONS[sunSign] || sunSign}
                      </span>
                    )}
                    {ascSign && (
                      <span className="text-violet/70">
                        AC {SIGN_TRANSLATIONS[ascSign] || ascSign}
                      </span>
                    )}
                  </div>

                  <div className="mt-5 text-center">
                    <span className="text-gold/50 text-sm group-hover:text-gold transition-colors">
                      Ver mapa &rarr;
                    </span>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}
