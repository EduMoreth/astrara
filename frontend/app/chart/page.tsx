'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'
import BirthForm from '@/components/BirthForm'
import ChartWheel from '@/components/ChartWheel'
import PlanetTable from '@/components/PlanetTable'
import { generateChart } from '@/lib/api'

interface ChartResult {
  positions: Record<string, { sign: string; deg: number }>
  houses: Array<{ sign: string; deg: number }>
  aspects: Array<{ p1: string; p2: string; aspect: string; orbit: number }>
}

export default function ChartPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ChartResult | null>(null)

  async function handleSubmit(data: {
    name: string
    year: number
    month: number
    day: number
    hour: number
    minute: number
    city: string
    country: string
  }) {
    setLoading(true)
    try {
      const res = await generateChart(data)
      setResult(res as ChartResult)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao gerar o mapa'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="relative min-h-screen">
      <StarBackground />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">
          Astrara
        </Link>
        <div className="flex items-center gap-4">
          <Link href="/auth/login" className="text-muted hover:text-stardust transition-colors text-sm">
            Entrar
          </Link>
        </div>
      </nav>

      <div className="relative z-10 px-6 py-12 max-w-6xl mx-auto">
        <AnimatePresence mode="wait">
          {/* ─── Loading overlay ───────────────── */}
          {loading && (
            <motion.div
              key="loading"
              className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-cosmos/90 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Animated mandala drawing */}
              <motion.svg
                viewBox="0 0 200 200"
                className="w-40 h-40"
                animate={{ rotate: 360 }}
                transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
              >
                <circle
                  cx="100" cy="100" r="85"
                  fill="none" stroke="rgba(201,169,110,0.3)"
                  strokeWidth="1.5"
                  strokeDasharray="534"
                  strokeDashoffset="534"
                >
                  <animate
                    attributeName="stroke-dashoffset"
                    from="534" to="0" dur="2s"
                    fill="freeze" repeatCount="indefinite"
                  />
                </circle>
                <circle
                  cx="100" cy="100" r="60"
                  fill="none" stroke="rgba(123,94,167,0.3)"
                  strokeWidth="1"
                  strokeDasharray="377"
                  strokeDashoffset="377"
                >
                  <animate
                    attributeName="stroke-dashoffset"
                    from="377" to="0" dur="2.5s"
                    fill="freeze" repeatCount="indefinite"
                  />
                </circle>
                <circle
                  cx="100" cy="100" r="35"
                  fill="none" stroke="rgba(201,169,110,0.2)"
                  strokeWidth="0.5"
                  strokeDasharray="220"
                  strokeDashoffset="220"
                >
                  <animate
                    attributeName="stroke-dashoffset"
                    from="220" to="0" dur="3s"
                    fill="freeze" repeatCount="indefinite"
                  />
                </circle>
              </motion.svg>

              <motion.p
                className="text-gold mt-8 text-lg font-display"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                Consultando os astros...
              </motion.p>
            </motion.div>
          )}

          {/* ─── Form ─────────────────────────── */}
          {!result && !loading && (
            <motion.div
              key="form"
              className="flex items-center justify-center min-h-[60vh]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <BirthForm onSubmit={handleSubmit} loading={loading} />
            </motion.div>
          )}

          {/* ─── Result ───────────────────────── */}
          {result && !loading && (
            <motion.div
              key="result"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6 }}
            >
              {/* Back to form */}
              <button
                onClick={() => setResult(null)}
                className="text-muted hover:text-stardust transition-colors text-sm mb-8 flex items-center gap-1"
              >
                &larr; Calcular novo mapa
              </button>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
                {/* Chart wheel */}
                <div>
                  <ChartWheel
                    positions={result.positions}
                    houses={result.houses}
                  />

                  <div className="flex justify-center mt-6">
                    <button
                      onClick={() => {
                        // TODO: implement SVG download
                        toast.success('Funcionalidade em breve!')
                      }}
                      className="btn-secondary text-sm"
                    >
                      Salvar mandala
                    </button>
                  </div>
                </div>

                {/* Planet table + CTA */}
                <div>
                  <PlanetTable positions={result.positions} />

                  {/* CTA card */}
                  <motion.div
                    className="glass-card p-8 mt-8 text-center border-gold/20"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 }}
                  >
                    <p className="text-stardust/80 text-lg font-display mb-6">
                      Quer entender o que esse mapa significa para voce?
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <Link href="/auth/register" className="btn-secondary text-sm">
                        Criar conta gratis
                      </Link>
                      <Link href="/auth/register" className="btn-primary text-sm">
                        Ver interpretacao completa &rarr;
                      </Link>
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}
