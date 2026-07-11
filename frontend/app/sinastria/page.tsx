'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'
import SynastryForm, { SynastryPersonData } from '@/components/SynastryForm'
import ChartWheel from '@/components/ChartWheel'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

interface DimensionScore {
  label: string
  score: number
  aspect_count: number
}

interface SynastryResult {
  chart_a: { positions: Record<string, { sign: string; deg: number }>; houses: Array<{ sign: string; deg: number }>; aspects: unknown[] }
  chart_b: { positions: Record<string, { sign: string; deg: number }>; houses: Array<{ sign: string; deg: number }>; aspects: unknown[] }
  inter_aspects: Array<{ p1: string; p2: string; aspect: string; orbit: number }>
  scores: { overall: number; dimensions: Record<string, DimensionScore> }
  credits_cost: number
}

const ASPECT_LABELS: Record<string, string> = {
  conjunction: 'Conjuncao', opposition: 'Oposicao', trine: 'Trigono',
  square: 'Quadratura', sextile: 'Sextil', quincunx: 'Quincuncio',
}

const PLANET_LABELS: Record<string, string> = {
  Sun: 'Sol', Moon: 'Lua', Mercury: 'Mercurio', Venus: 'Venus', Mars: 'Marte',
  Jupiter: 'Jupiter', Saturn: 'Saturno', Uranus: 'Urano', Neptune: 'Netuno',
  Pluto: 'Plutao', Ascendant: 'Ascendente', Midheaven: 'Meio do Ceu',
}

const HARMONIOUS = new Set(['trine', 'sextile', 'conjunction'])

function SinastriaContent() {
  const router = useRouter()
  const params = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SynastryResult | null>(null)
  const [names, setNames] = useState<{ a: string; b: string }>({ a: 'Pessoa 1', b: 'Pessoa 2' })
  const [downloading, setDownloading] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [product, setProduct] = useState<{ id: string | null; name: string; price_cents: number } | null>(null)

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem('astrara_token'))

    fetch(`${API_URL}/chart/synastry-product`)
      .then(r => (r.ok ? r.json() : null))
      .then(data => { if (data && typeof data.price_cents === 'number') setProduct(data) })
      .catch(() => {})

    // Restore a previous result (e.g. returning from Stripe checkout)
    try {
      const saved = sessionStorage.getItem('astrara_synastry_result')
      const savedNames = sessionStorage.getItem('astrara_synastry_names')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (parsed && parsed.chart_a && parsed.scores) setResult(parsed)
      }
      if (savedNames) {
        const n = JSON.parse(savedNames)
        if (n && n.a && n.b) setNames(n)
      }
    } catch { /* ignore */ }

    // Returning from payment: verify the session so credits land immediately
    const sessionId = params.get('session_id')
    const token = localStorage.getItem('astrara_token')
    if (sessionId && token) {
      fetch(`${API_URL}/checkout/verify/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            toast.success('Pagamento confirmado! Clique em "Baixar analise completa".')
            window.history.replaceState({}, '', '/sinastria')
          }
        })
        .catch(() => {})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleSubmit(personA: SynastryPersonData, personB: SynastryPersonData) {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/chart/synastry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ person_a: personA, person_b: personB }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Erro ao calcular a sinastria')
      }
      const data: SynastryResult = await res.json()
      setResult(data)
      setNames({ a: personA.name, b: personB.name })
      try {
        sessionStorage.setItem('astrara_synastry_result', JSON.stringify(data))
        sessionStorage.setItem('astrara_synastry_names', JSON.stringify({ a: personA.name, b: personB.name }))
      } catch { /* storage full: continue without cache */ }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao calcular a sinastria')
    } finally {
      setLoading(false)
    }
  }

  async function handleUnlock() {
    if (!result) return

    const token = localStorage.getItem('astrara_token')
    if (!token) {
      sessionStorage.setItem('astrara_intent', 'buy_sinastria')
      toast.error('Crie uma conta para desbloquear a analise completa.')
      router.push('/auth/register')
      return
    }

    setDownloading(true)
    toast.info('Gerando analise de sinastria com IA... Isso pode levar ate 1 minuto.')
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 180000)

      const res = await fetch(`${API_URL}/chart/synastry/generate-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          person_a: { name: names.a, positions: result.chart_a.positions },
          person_b: { name: names.b, positions: result.chart_b.positions },
        }),
        signal: controller.signal,
      })
      clearTimeout(timeoutId)

      if (res.status === 402) {
        // No credits — send to Stripe checkout for the Sinastria product
        if (!product?.id) {
          toast.error('Produto Sinastria nao configurado. Contate o suporte.')
          return
        }
        const checkoutRes = await fetch(`${API_URL}/checkout/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ product_id: product.id }),
        })
        if (!checkoutRes.ok) {
          const err = await checkoutRes.json().catch(() => ({}))
          throw new Error(typeof err.detail === 'string' ? err.detail : 'Erro ao iniciar pagamento')
        }
        const data = await checkoutRes.json()
        if (data.checkout_url) {
          if (data.session_id) localStorage.setItem('astrara_payment_session', data.session_id)
          // Return to /sinastria (not /chart) after payment
          try { localStorage.setItem('astrara_checkout_return', '/sinastria') } catch { /* ignore */ }
          const { openExternalUrl } = await import('@/lib/navigation')
          await openExternalUrl(data.checkout_url)
        }
        return
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Erro ao gerar analise' }))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Erro ao gerar analise')
      }

      const blob = await res.blob()
      const { downloadFile } = await import('@/lib/download')
      await downloadFile(blob, `astrara-sinastria-${names.a.toLowerCase()}-${names.b.toLowerCase()}.pdf`.replace(/\s+/g, '-'))
      toast.success('Analise de sinastria baixada com sucesso!')
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        toast.error('A geracao demorou demais. Tente novamente em alguns minutos.')
      } else {
        toast.error(err instanceof Error ? err.message : 'Erro ao gerar analise')
      }
    } finally {
      setDownloading(false)
    }
  }

  const priceLabel = product
    ? `R$ ${(product.price_cents / 100).toFixed(2).replace('.', ',')}`
    : 'R$ 78,00'

  const scoreColor = (v: number) => (v >= 70 ? '#44FF88' : v >= 45 ? '#C9A96E' : '#FF6644')

  return (
    <main className="relative min-h-screen">
      <StarBackground />

      <nav className="relative z-10 flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">Astrara</Link>
        <div className="flex items-center gap-4">
          <Link href="/chart" className="text-muted hover:text-stardust transition-colors text-sm">Mapa individual</Link>
          {isLoggedIn ? (
            <Link href="/dashboard" className="text-muted hover:text-stardust transition-colors text-sm">Meus mapas</Link>
          ) : (
            <Link href="/auth/login" className="text-muted hover:text-stardust transition-colors text-sm">Entrar</Link>
          )}
        </div>
      </nav>

      <div className="relative z-10 px-4 sm:px-6 py-6 sm:py-12 max-w-6xl mx-auto">
        <AnimatePresence mode="wait">
          {!result && (
            <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <SynastryForm onSubmit={handleSubmit} loading={loading} />
            </motion.div>
          )}

          {result && (
            <motion.div key="result" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
              <button
                onClick={() => {
                  setResult(null)
                  sessionStorage.removeItem('astrara_synastry_result')
                  sessionStorage.removeItem('astrara_synastry_names')
                }}
                className="text-muted hover:text-stardust transition-colors text-sm mb-8 flex items-center gap-1">
                &larr; Nova sinastria
              </button>

              {/* Overall score */}
              <div className="text-center mb-10">
                <h1 className="font-display text-2xl sm:text-3xl text-stardust mb-1">
                  {names.a} <span className="text-gold">&hearts;</span> {names.b}
                </h1>
                <p className="text-muted text-sm mb-6">Afinidade astral entre os dois mapas</p>
                <motion.div
                  className="inline-flex flex-col items-center justify-center w-36 h-36 rounded-full border-2"
                  style={{ borderColor: scoreColor(result.scores.overall) }}
                  initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.2 }}
                >
                  <span className="font-display text-5xl" style={{ color: scoreColor(result.scores.overall) }}>
                    {result.scores.overall}
                  </span>
                  <span className="text-muted text-xs mt-1">de 100</span>
                </motion.div>
              </div>

              {/* Dimension scores */}
              <div className="glass-card p-6 sm:p-8 mb-10 max-w-2xl mx-auto">
                <h2 className="font-display text-lg text-stardust mb-6 text-center">Afinidade por dimensao</h2>
                <div className="space-y-4">
                  {Object.entries(result.scores.dimensions).map(([key, dim]) => (
                    <div key={key}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-stardust/80">{dim.label}</span>
                        <span style={{ color: scoreColor(dim.score) }}>{dim.score}</span>
                      </div>
                      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div className="h-full rounded-full"
                          style={{ backgroundColor: scoreColor(dim.score) }}
                          initial={{ width: 0 }} animate={{ width: `${dim.score}%` }} transition={{ duration: 0.8, delay: 0.3 }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Two wheels side by side */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
                <div>
                  <h3 className="font-display text-center text-stardust mb-3">{names.a}</h3>
                  <ChartWheel positions={result.chart_a.positions} houses={result.chart_a.houses}
                    aspects={result.chart_a.aspects as never} birthName={names.a} />
                </div>
                <div>
                  <h3 className="font-display text-center text-stardust mb-3">{names.b}</h3>
                  <ChartWheel positions={result.chart_b.positions} houses={result.chart_b.houses}
                    aspects={result.chart_b.aspects as never} birthName={names.b} />
                </div>
              </div>

              {/* Inter-aspects table */}
              <div className="glass-card p-6 sm:p-8 mb-10 max-w-2xl mx-auto overflow-x-auto">
                <h2 className="font-display text-lg text-stardust mb-4 text-center">
                  Aspectos entre os mapas ({result.inter_aspects.length})
                </h2>
                {result.inter_aspects.length === 0 ? (
                  <p className="text-muted text-sm text-center">Nenhum aspecto maior encontrado entre os mapas.</p>
                ) : (
                  <table className="w-full min-w-[320px] text-sm">
                    <thead>
                      <tr className="border-b border-gold/10 text-muted text-xs uppercase tracking-wider">
                        <th className="text-left py-2">{names.a}</th>
                        <th className="text-center py-2">Aspecto</th>
                        <th className="text-right py-2">{names.b}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.inter_aspects.map((a, i) => (
                        <tr key={i} className="border-b border-white/[0.03]">
                          <td className="py-2 text-stardust/80">{PLANET_LABELS[a.p1] || a.p1}</td>
                          <td className="py-2 text-center" style={{ color: HARMONIOUS.has(a.aspect) ? '#44FF88' : '#FF6644' }}>
                            {ASPECT_LABELS[a.aspect] || a.aspect}
                          </td>
                          <td className="py-2 text-right text-stardust/80">{PLANET_LABELS[a.p2] || a.p2}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* CTA */}
              <motion.div className="glass-card p-8 text-center border-gold/20 max-w-2xl mx-auto"
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
                <div className="text-3xl mb-3">&#128152;</div>
                <p className="text-stardust/80 text-lg font-display mb-4">
                  Quer entender o que esses aspectos significam para o relacionamento?
                </p>
                <p className="text-muted text-sm mb-6">
                  Receba a analise completa da sinastria: cada aspecto entre os planetas dos dois mapas
                  interpretado por IA, com desafios, potenciais e conselhos para o casal. Inclui PDF para download.
                </p>
                <button onClick={handleUnlock} disabled={downloading} className="btn-primary text-sm disabled:opacity-50">
                  {downloading ? 'Gerando analise...' : `Baixar analise completa — ${priceLabel} →`}
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}

export default function SinastriaPage() {
  return (
    <Suspense fallback={
      <main className="relative min-h-screen flex items-center justify-center">
        <div className="text-muted">Carregando...</div>
      </main>
    }>
      <SinastriaContent />
    </Suspense>
  )
}
