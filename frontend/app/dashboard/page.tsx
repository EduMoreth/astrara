'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'
import { getUserCharts } from '@/lib/api'
import { getUserFromToken, removeToken } from '@/lib/auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

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

interface ChartLimit {
  saved_count: number
  max_charts: number
  can_save: boolean
}

const SIGN_TRANSLATIONS: Record<string, string> = {
  Aries: 'Aries', Ari: 'Aries',
  Taurus: 'Touro', Tau: 'Touro',
  Gemini: 'Gemeos', Gem: 'Gemeos',
  Cancer: 'Cancer', Can: 'Cancer',
  Leo: 'Leao',
  Virgo: 'Virgem', Vir: 'Virgem',
  Libra: 'Libra', Lib: 'Libra',
  Scorpio: 'Escorpiao', Sco: 'Escorpiao',
  Sagittarius: 'Sagitario', Sag: 'Sagitario',
  Capricorn: 'Capricornio', Cap: 'Capricornio',
  Aquarius: 'Aquario', Aqu: 'Aquario',
  Pisces: 'Peixes', Pis: 'Peixes',
}

function getHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('astrara_token') : null
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
}

export default function DashboardPage() {
  const router = useRouter()
  const [charts, setCharts] = useState<Chart[]>([])
  const [loading, setLoading] = useState(true)
  const [limits, setLimits] = useState<ChartLimit | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const user = getUserFromToken()

  function loadData() {
    if (!user) return
    getUserCharts()
      .then(setCharts)
      .catch(() => toast.error('Erro ao carregar seus mapas'))
      .finally(() => setLoading(false))

    fetch(`${API_URL}/user/charts/limit`, { headers: getHeaders() })
      .then(r => r.json())
      .then(setLimits)
      .catch(() => {})
  }

  useEffect(() => {
    if (!user) { router.push('/auth/login'); return }
    loadData()
  }, [])

  async function handleDelete(chartId: string) {
    try {
      const res = await fetch(`${API_URL}/user/charts/${chartId}`, {
        method: 'DELETE', headers: getHeaders(),
      })
      if (!res.ok) throw new Error('Erro ao deletar')
      toast.success('Mapa deletado')
      setConfirmDelete(null)
      loadData()
    } catch {
      toast.error('Erro ao deletar mapa')
    }
  }

  if (!user) return null

  const maxDisplay = limits?.max_charts === 999999 ? '∞' : String(limits?.max_charts || '?')

  return (
    <main className="relative min-h-screen">
      <StarBackground />

      <header className="relative z-10 flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-xl sm:text-2xl font-semibold text-gradient-gold">Astrara</Link>
        <div className="flex items-center gap-2 sm:gap-5">
          <Link href="/conta" className="text-muted hover:text-stardust text-xs sm:text-sm hidden sm:inline">Minha conta</Link>
          <Link href="/support" className="text-muted hover:text-stardust text-xs sm:text-sm hidden sm:inline">Suporte</Link>
          <span className="text-stardust text-xs sm:text-sm truncate max-w-[100px] sm:max-w-none">{user.name}</span>
          <button onClick={() => { removeToken(); router.push('/') }} className="text-muted hover:text-stardust text-xs sm:text-sm">Sair</button>
        </div>
      </header>

      <div className="relative z-10 px-4 sm:px-6 py-6 sm:py-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-3xl font-light text-stardust">Meus mapas</h1>
            {limits && (
              <p className="text-muted text-sm mt-1">
                {limits.saved_count} de {maxDisplay} mapas salvos
                {limits.max_charts === 1 && (
                  <span className="text-gold/60 ml-2">(plano gratuito)</span>
                )}
              </p>
            )}
          </div>
          <Link href="/chart" className="btn-primary text-sm">+ Novo mapa</Link>
        </div>

        {loading && (
          <div className="flex justify-center py-20">
            <motion.div className="w-8 h-8 border-2 border-gold/30 border-t-gold rounded-full" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }} />
          </div>
        )}

        {!loading && charts.length === 0 && (
          <motion.div className="glass-card p-16 text-center max-w-lg mx-auto" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="text-6xl mb-6 opacity-30">✨</div>
            <h2 className="font-display text-xl text-stardust mb-3">Nenhum mapa salvo ainda</h2>
            <p className="text-muted text-sm mb-8">Calcule seu mapa astral e clique em &quot;Salvar mapa na minha conta&quot;.</p>
            <Link href="/chart" className="btn-primary">Criar meu primeiro mapa</Link>
          </motion.div>
        )}

        {!loading && charts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {charts.map((chart, i) => {
              const sunSign = chart.positions_json?.sun?.sign || ''
              const moonSign = chart.positions_json?.moon?.sign || ''
              const ascSign = chart.positions_json?.ascendant?.sign || ''

              return (
                <motion.div
                  key={chart.id}
                  className="glass-card p-6 group"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full border border-gold/15 flex items-center justify-center">
                    <svg viewBox="0 0 100 100" className="w-10 h-10 opacity-40">
                      <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(201,169,110,0.3)" strokeWidth="1" />
                      <circle cx="50" cy="50" r="30" fill="none" stroke="rgba(123,94,167,0.3)" strokeWidth="0.5" />
                    </svg>
                  </div>

                  <h3 className="text-stardust font-medium text-center text-lg">{chart.name}</h3>
                  <p className="text-muted text-xs text-center mt-1">
                    {chart.birth_date} &middot; {chart.birth_city}
                  </p>

                  <div className="flex justify-center gap-3 mt-3 text-xs">
                    {sunSign && <span className="text-gold/70">☉ {SIGN_TRANSLATIONS[sunSign] || sunSign}</span>}
                    {moonSign && <span className="text-violet/70">☽ {SIGN_TRANSLATIONS[moonSign] || moonSign}</span>}
                    {ascSign && <span className="text-muted">AC {SIGN_TRANSLATIONS[ascSign] || ascSign}</span>}
                  </div>

                  <div className="flex justify-center gap-3 mt-5">
                    <button
                      onClick={async () => {
                        // Re-generate chart from saved birth data
                        const [y, m, d] = (chart.birth_date || '').split('-')
                        const [hr, mn] = (chart.birth_time || '12:00').split(':')
                        const formData = {
                          name: chart.name,
                          year: parseInt(y || '2000'),
                          month: parseInt(m || '1'),
                          day: parseInt(d || '1'),
                          hour: parseInt(hr || '12'),
                          minute: parseInt(mn || '0'),
                          city: chart.birth_city || '',
                          country: '',
                        }
                        // Save form data so chart page shows birth info
                        sessionStorage.setItem('astrara_last_form', JSON.stringify(formData))
                        // Remove old result so chart page recalculates
                        sessionStorage.removeItem('astrara_chart_result')
                        // Set flag to auto-generate on chart page load
                        sessionStorage.setItem('astrara_auto_generate', JSON.stringify(formData))
                        router.push('/chart')
                      }}
                      className="text-gold hover:text-gold/80 text-xs transition-colors"
                    >
                      Ver mapa →
                    </button>

                    {confirmDelete === chart.id ? (
                      <>
                        <button onClick={() => handleDelete(chart.id)} className="text-[#E74C3C] text-xs font-bold">Confirmar exclusao?</button>
                        <button onClick={() => setConfirmDelete(null)} className="text-muted text-xs">Cancelar</button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => setConfirmDelete(chart.id)} className="text-muted hover:text-[#E74C3C] text-xs transition-colors">
                          Deletar
                        </button>
                      </>
                    )}
                  </div>

                  <p className="text-muted/30 text-[10px] text-center mt-3">
                    Salvo em {new Date(chart.created_at).toLocaleDateString('pt-BR')}
                  </p>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}
