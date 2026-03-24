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
    // Save form data for later use by save endpoint
    sessionStorage.setItem('astrara_last_form', JSON.stringify(data))
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

  async function handleInterpretationClick() {
    // STEP 1: Must be logged in
    if (!isLoggedIn) {
      sessionStorage.setItem('astrara_intent', 'buy_interpretation')
      toast.error('Voce precisa criar uma conta antes de desbloquear a interpretacao.')
      router.push('/auth/register')
      return
    }

    const token = localStorage.getItem('astrara_token')
    if (!token) {
      toast.error('Sessao expirada. Faca login novamente.')
      router.push('/auth/login')
      return
    }

    // STEP 2: Check access via single backend endpoint
    try {
      const accessRes = await fetch(`${API_URL}/chart/check-interpretation-access`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!accessRes.ok) {
        console.error('Access check failed:', accessRes.status)
        toast.error('Erro ao verificar acesso. Tente novamente.')
        return
      }

      const access = await accessRes.json()
      console.log('Access check result:', access)

      if (access.has_access) {
        // User has credits or purchase — show PDF download directly!
        if (access.reason === 'has_credits') {
          toast.success(`Voce tem ${access.credits} credito(s)! Gerando interpretacao...`)
        } else {
          toast.success('Interpretacao desbloqueada! Gerando PDF...')
        }
        setPaidRecently(true)
        return
      }
    } catch (err) {
      console.error('Access check error:', err)
      toast.error('Erro ao verificar creditos. Tente novamente.')
      return
    }

    // STEP 3: No access — redirect to Stripe checkout
    if (!interpProduct?.id) {
      toast.error('Produto de interpretacao nao configurado. Contate o suporte.')
      return
    }

    try {
      const res = await fetch(`${API_URL}/checkout/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ product_id: interpProduct.id }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Erro')
      }
      const data = await res.json()
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao iniciar pagamento')
    }
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
                  <ChartWheel
                    positions={result.positions}
                    houses={result.houses}
                    aspects={result.aspects}
                    birthName={(() => { try { const f = JSON.parse(sessionStorage.getItem('astrara_last_form') || '{}'); return f.name } catch { return '' } })()}
                    birthDate={(() => { try { const f = JSON.parse(sessionStorage.getItem('astrara_last_form') || '{}'); return f.day && f.month && f.year ? `${String(f.day).padStart(2,'0')}/${String(f.month).padStart(2,'0')}/${f.year}` : '' } catch { return '' } })()}
                    birthTime={(() => { try { const f = JSON.parse(sessionStorage.getItem('astrara_last_form') || '{}'); return f.hour !== undefined ? `${String(f.hour).padStart(2,'0')}:${String(f.minute).padStart(2,'0')}` : '' } catch { return '' } })()}
                    birthCity={(() => { try { const f = JSON.parse(sessionStorage.getItem('astrara_last_form') || '{}'); return f.city || '' } catch { return '' } })()}
                  />
                  {/* Save to account + Download */}
                  <div className="space-y-3 mt-6">
                    <div className="flex justify-center gap-3">
                      {/* Save to DB */}
                      {isLoggedIn ? (
                        <button
                          onClick={async () => {
                            const token = localStorage.getItem('astrara_token')
                            if (!token) { toast.error('Faca login para salvar'); return }
                            try {
                              const formData = sessionStorage.getItem('astrara_last_form')
                              const form = formData ? JSON.parse(formData) : {}
                              const res = await fetch(`${API_URL}/user/charts/save`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                                body: JSON.stringify({
                                  name: form.name || 'Meu Mapa',
                                  birth_date: form.year ? `${form.year}-${String(form.month).padStart(2,'0')}-${String(form.day).padStart(2,'0')}` : '2000-01-01',
                                  birth_time: form.hour !== undefined ? `${String(form.hour).padStart(2,'0')}:${String(form.minute).padStart(2,'0')}` : '12:00',
                                  birth_city: form.city || '',
                                  birth_country: form.country || '',
                                  positions_json: result?.positions || {},
                                }),
                              })
                              if (!res.ok) {
                                const err = await res.json()
                                throw new Error(err.detail || 'Erro ao salvar')
                              }
                              const data = await res.json()
                              toast.success(`Mapa salvo! (${data.saved_count}/${data.max_charts === 999999 ? '∞' : data.max_charts})`)
                            } catch (err: unknown) {
                              toast.error(err instanceof Error ? err.message : 'Erro ao salvar mapa')
                            }
                          }}
                          className="btn-primary text-sm"
                        >
                          Salvar mapa na minha conta
                        </button>
                      ) : (
                        <Link href="/auth/register" className="btn-primary text-sm">
                          Criar conta para salvar
                        </Link>
                      )}

                      {/* Download JPG only */}
                      <button
                        onClick={() => {
                          const svgEl = document.querySelector('.chart-wheel-svg') as SVGSVGElement
                          if (!svgEl) { toast.error('Mandala nao encontrada'); return }
                          const canvas = document.createElement('canvas')
                          canvas.width = 1200; canvas.height = 1200
                          const ctx = canvas.getContext('2d')
                          if (!ctx) return
                          ctx.fillStyle = '#0A0A0F'
                          ctx.fillRect(0, 0, 1200, 1200)
                          const img = new Image()
                          img.onload = () => {
                            ctx.drawImage(img, 0, 0, 1200, 1200)
                            const a = document.createElement('a')
                            a.href = canvas.toDataURL('image/jpeg', 0.95)
                            a.download = 'astrara-mandala.jpg'
                            a.click()
                            toast.success('Mandala baixada!')
                          }
                          img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(new XMLSerializer().serializeToString(svgEl))))
                        }}
                        className="btn-secondary text-sm"
                      >
                        Baixar mandala
                      </button>
                    </div>
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
