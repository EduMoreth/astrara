'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'
import BirthForm from '@/components/BirthForm'
import ChartWheel from '@/components/ChartWheel'
import PlanetTable from '@/components/PlanetTable'
import { generateChart, ChartResponse } from '@/lib/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

interface InterpProduct {
  id: string | null
  name: string
  price_cents: number
}

export default function ChartPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ChartResponse | null>(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [interpProduct, setInterpProduct] = useState<InterpProduct | null>(null)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('astrara_token')
    setIsLoggedIn(!!token)

    // Fetch interpretation product info
    fetch(`${API_URL}/chart/interpretation-product`)
      .then(r => r.json())
      .then(setInterpProduct)
      .catch(() => {})

    // Restore chart result from sessionStorage (survives auth/payment redirects)
    const saved = sessionStorage.getItem('astrara_chart_result')
    if (saved) {
      try {
        setResult(JSON.parse(saved))
      } catch { /* ignore */ }
    }
  }, [])

  // Save result to sessionStorage whenever it changes
  useEffect(() => {
    if (result) {
      sessionStorage.setItem('astrara_chart_result', JSON.stringify(result))
    }
  }, [result])

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
      setResult(res as ChartResponse)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao gerar o mapa'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  function handleInterpretationClick() {
    // STEP 1: Must be logged in
    if (!isLoggedIn) {
      // Save intent so after login we come back
      sessionStorage.setItem('astrara_intent', 'buy_interpretation')
      toast.error('Voce precisa criar uma conta antes de comprar a interpretacao.')
      router.push('/auth/register')
      return
    }

    // STEP 2: Must have a product configured
    if (!interpProduct?.id) {
      toast.error('Produto de interpretacao nao configurado. Contate o suporte.')
      return
    }

    // STEP 3: Redirect to Stripe checkout
    const token = localStorage.getItem('astrara_token')
    fetch(`${API_URL}/checkout/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ product_id: interpProduct.id }),
    })
      .then(r => {
        if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Erro') })
        return r.json()
      })
      .then(data => {
        if (data.checkout_url) {
          window.location.href = data.checkout_url
        }
      })
      .catch((err: Error) => {
        toast.error(err.message || 'Erro ao iniciar pagamento')
      })
  }

  async function handleDownloadPdf() {
    // This is called after payment is confirmed
    // For now we need a chart_id from the backend — use positions as fallback
    setDownloadingPdf(true)
    try {
      const token = localStorage.getItem('astrara_token')
      if (!token) {
        toast.error('Faca login para baixar o PDF')
        return
      }
      // Use a special endpoint that generates PDF from positions directly
      const res = await fetch(`${API_URL}/chart/interpretation/generate-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          positions: result?.positions,
          name: 'Meu Mapa Astral',
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Erro ao gerar PDF' }))
        throw new Error(err.detail)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'astrara-interpretacao.pdf'
      a.click()
      URL.revokeObjectURL(url)
      toast.success('PDF baixado com sucesso!')
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao gerar PDF')
    } finally {
      setDownloadingPdf(false)
    }
  }

  // Check if user just returned from payment
  const [paidRecently, setPaidRecently] = useState(false)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const sessionId = urlParams.get('session_id')
    if (sessionId && isLoggedIn) {
      // Verify payment
      const token = localStorage.getItem('astrara_token')
      fetch(`${API_URL}/checkout/verify/${sessionId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            setPaidRecently(true)
            toast.success('Pagamento confirmado! Clique em "Baixar interpretacao em PDF".')
            // Clean URL
            window.history.replaceState({}, '', '/chart')
          }
        })
        .catch(() => {})
    }
  }, [isLoggedIn])

  const priceLabel = interpProduct
    ? `R$ ${(interpProduct.price_cents / 100).toFixed(2).replace('.', ',')}`
    : 'R$ 29,90'

  return (
    <main className="relative min-h-screen">
      <StarBackground />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">
          Astrara
        </Link>
        <div className="flex items-center gap-4">
          {isLoggedIn ? (
            <Link href="/dashboard" className="text-muted hover:text-stardust transition-colors text-sm">
              Meus mapas
            </Link>
          ) : (
            <Link href="/auth/login" className="text-muted hover:text-stardust transition-colors text-sm">
              Entrar
            </Link>
          )}
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
              <motion.svg
                viewBox="0 0 200 200"
                className="w-40 h-40"
                animate={{ rotate: 360 }}
                transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
              >
                <circle cx="100" cy="100" r="85" fill="none" stroke="rgba(201,169,110,0.3)" strokeWidth="1.5" strokeDasharray="534" strokeDashoffset="534">
                  <animate attributeName="stroke-dashoffset" from="534" to="0" dur="2s" fill="freeze" repeatCount="indefinite" />
                </circle>
                <circle cx="100" cy="100" r="60" fill="none" stroke="rgba(123,94,167,0.3)" strokeWidth="1" strokeDasharray="377" strokeDashoffset="377">
                  <animate attributeName="stroke-dashoffset" from="377" to="0" dur="2.5s" fill="freeze" repeatCount="indefinite" />
                </circle>
              </motion.svg>
              <motion.p className="text-gold mt-8 text-lg font-display" animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 2, repeat: Infinity }}>
                Consultando os astros...
              </motion.p>
            </motion.div>
          )}

          {/* ─── Form ─────────────────────────── */}
          {!result && !loading && (
            <motion.div key="form" className="flex items-center justify-center min-h-[60vh]" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <BirthForm onSubmit={handleSubmit} loading={loading} />
            </motion.div>
          )}

          {/* ─── Result ───────────────────────── */}
          {result && !loading && (
            <motion.div key="result" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
              <button onClick={() => { setResult(null); sessionStorage.removeItem('astrara_chart_result') }}
                className="text-muted hover:text-stardust transition-colors text-sm mb-8 flex items-center gap-1">
                &larr; Calcular novo mapa
              </button>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
                {/* Chart wheel */}
                <div>
                  <ChartWheel positions={result.positions} houses={result.houses} aspects={result.aspects} />
                  <div className="flex justify-center mt-6">
                    <button onClick={() => toast.success('Funcionalidade em breve!')} className="btn-secondary text-sm">
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
                    {paidRecently ? (
                      <>
                        <div className="text-3xl mb-3">✨</div>
                        <p className="text-gold text-lg font-display mb-2">Interpretacao desbloqueada!</p>
                        <p className="text-muted text-sm mb-6">Clique abaixo para baixar seu PDF personalizado com a interpretacao completa.</p>
                        <button
                          onClick={handleDownloadPdf}
                          disabled={downloadingPdf}
                          className="btn-primary text-sm"
                        >
                          {downloadingPdf ? 'Gerando PDF...' : 'Baixar interpretacao em PDF'}
                        </button>
                      </>
                    ) : (
                      <>
                        <p className="text-stardust/80 text-lg font-display mb-6">
                          Quer entender o que esse mapa significa para voce?
                        </p>
                        <p className="text-muted text-sm mb-6">
                          Receba uma interpretacao completa de cada planeta, casa e aspecto do seu mapa, gerada por inteligencia artificial. Inclui PDF para download.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-3 justify-center">
                          {isLoggedIn ? (
                            <button onClick={handleInterpretationClick} className="btn-primary text-sm">
                              Desbloquear interpretacao — {priceLabel} &rarr;
                            </button>
                          ) : (
                            <>
                              <Link href="/auth/login" className="btn-secondary text-sm">
                                Ja tenho conta
                              </Link>
                              <button onClick={handleInterpretationClick} className="btn-primary text-sm">
                                Criar conta e desbloquear — {priceLabel} &rarr;
                              </button>
                            </>
                          )}
                        </div>
                      </>
                    )}
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
