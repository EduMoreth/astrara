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
      .then(r => (r.ok ? r.json() : null))
      .then(data => {
        if (data && typeof data.price_cents === 'number') setInterpProduct(data)
      })
      .catch(() => {})

    // First check if there's a cached chart result (e.g. from dashboard "Ver mapa")
    const saved = sessionStorage.getItem('astrara_chart_result')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        // Validate shape — a malformed cached value (e.g. from an older app
        // version) would crash the wheel and persist across reloads
        if (parsed && typeof parsed.positions === 'object' && parsed.positions !== null) {
          setResult(parsed)
        } else {
          sessionStorage.removeItem('astrara_chart_result')
        }
      } catch {
        sessionStorage.removeItem('astrara_chart_result')
      }
      // Don't auto-generate if we already have a result
      sessionStorage.removeItem('astrara_auto_generate')
      return
    }

    // Check if coming from dashboard with auto-generate flag (only if no cached result)
    const autoGen = sessionStorage.getItem('astrara_auto_generate')
    if (autoGen) {
      sessionStorage.removeItem('astrara_auto_generate')
      try {
        const formData = JSON.parse(autoGen)
        handleSubmit(formData)
      } catch { /* ignore */ }
      return
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
      // Embed the birth form inside the result so the two never separate
      // (a save without birth data would create a nameless/cityless chart)
      setResult({ ...(res as ChartResponse), form: data } as ChartResponse)
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
        // Save session_id so we can verify payment when browser closes (mobile)
        if (data.session_id) {
          localStorage.setItem('astrara_payment_session', data.session_id)
        }
        const { openExternalUrl } = await import('@/lib/navigation')
        await openExternalUrl(data.checkout_url)
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao iniciar pagamento')
    }
  }

  async function handleDownloadPdf() {
    setDownloadingPdf(true)
    toast.info('Gerando interpretacao com IA... Isso pode levar ate 1 minuto.')
    try {
      const token = localStorage.getItem('astrara_token')
      if (!token) {
        toast.error('Faca login para baixar o PDF')
        return
      }
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 180000) // 3 min timeout

      const res = await fetch(`${API_URL}/chart/interpretation/generate-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          positions: result?.positions,
          // Personalize the interpretation/PDF with the person's real name
          name: (() => {
            try {
              const f = JSON.parse(sessionStorage.getItem('astrara_last_form') || '{}')
              return f.name || 'Meu Mapa Astral'
            } catch { return 'Meu Mapa Astral' }
          })(),
        }),
        signal: controller.signal,
      })
      clearTimeout(timeoutId)

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Erro ao gerar PDF' }))
        throw new Error(err.detail)
      }
      const blob = await res.blob()
      const { downloadFile } = await import('@/lib/download')
      await downloadFile(blob, 'astrara-interpretacao.pdf')
      toast.success('PDF baixado com sucesso!')
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        toast.error('A geracao do PDF demorou demais. Por favor, tente novamente em alguns minutos.')
      } else {
        const msg = err instanceof Error ? err.message : 'Erro ao gerar PDF'
        toast.error(`Erro ao gerar PDF: ${msg}. Se o problema persistir, entre em contato com o suporte.`)
      }
    } finally {
      setDownloadingPdf(false)
    }
  }

  // Check if user just returned from payment or already has credits
  const [paidRecently, setPaidRecently] = useState(false)
  useEffect(() => {
    if (!isLoggedIn) return

    const token = localStorage.getItem('astrara_token')
    if (!token) return

    // Check for payment return — from URL params (web) or localStorage (mobile)
    const urlParams = new URLSearchParams(window.location.search)
    let sessionId = urlParams.get('session_id')

    // On mobile, the in-app browser stores the session_id in localStorage before closing
    if (!sessionId) {
      sessionId = localStorage.getItem('astrara_payment_session')
      if (sessionId) localStorage.removeItem('astrara_payment_session')
    }

    if (sessionId) {
      // Try to verify (this is now idempotent — safe if webhook already fulfilled)
      fetch(`${API_URL}/checkout/verify/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            setPaidRecently(true)
            toast.success('Pagamento confirmado! Clique em "Baixar interpretacao em PDF".')
            window.history.replaceState({}, '', '/chart')
          }
        })
        .catch(() => {
          // Verify failed (maybe network issue), but webhook may have added credits.
          // Fall through to the credits check below.
        })
        .finally(() => {
          // Always check credits as a fallback — webhook may have already delivered them
          _checkCreditsAndUnlock(token)
        })
    } else {
      // No session_id, but user might have credits from webhook or previous purchase
      // Check on every chart page load so returning users see their interpretation
      _checkCreditsAndUnlock(token)
    }

    // On mobile, also listen for browser close event to re-check payment.
    // Keep the listener handle and remove it on cleanup — otherwise every
    // re-run of this effect stacks another listener (duplicate verifies and
    // toasts) and the old one fires on an unmounted component.
    let removed = false
    let browserListener: { remove: () => Promise<void> } | null = null
    if (typeof window !== 'undefined') {
      import('@capacitor/core').then(({ Capacitor }) => {
        if (Capacitor.isNativePlatform()) {
          import('@capacitor/browser').then(({ Browser }) => {
            Browser.addListener('browserFinished', () => {
              const pendingSession = localStorage.getItem('astrara_payment_session')
              if (pendingSession) {
                localStorage.removeItem('astrara_payment_session')
                const tk = localStorage.getItem('astrara_token')
                if (tk) {
                  fetch(`${API_URL}/checkout/verify/${pendingSession}`, {
                    headers: { Authorization: `Bearer ${tk}` },
                  })
                    .then(r => r.json())
                    .then(data => {
                      if (data.success) {
                        setPaidRecently(true)
                        toast.success('Pagamento confirmado! Clique em "Baixar interpretacao em PDF".')
                      }
                    })
                    .catch(() => {})
                    .finally(() => _checkCreditsAndUnlock(tk))
                }
              }
            }).then(handle => {
              if (removed) handle.remove()
              else browserListener = handle
            })
          })
        }
      })
    }
    return () => {
      removed = true
      browserListener?.remove()
    }
  }, [isLoggedIn])

  /** Check if user has credits/purchase and auto-unlock interpretation */
  function _checkCreditsAndUnlock(token: string) {
    fetch(`${API_URL}/chart/check-interpretation-access`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(access => {
        if (access.has_access && !paidRecently) {
          setPaidRecently(true)
        }
      })
      .catch(() => {})
  }

  const priceLabel = interpProduct
    ? `R$ ${(interpProduct.price_cents / 100).toFixed(2).replace('.', ',')}`
    : 'R$ 29,90'

  return (
    <main className="relative min-h-screen">
      <StarBackground />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">
          Astrara
        </Link>
        <div className="flex items-center gap-4">
          <Link href="/sinastria" className="text-muted hover:text-stardust transition-colors text-sm">
            Sinastria
          </Link>
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

      <div className="relative z-10 px-4 sm:px-6 py-6 sm:py-12 max-w-6xl mx-auto">
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

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-12 items-start">
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
                    <div className="flex flex-col sm:flex-row justify-center gap-3">
                      {/* Save to DB */}
                      {isLoggedIn ? (
                        <button
                          onClick={async () => {
                            const token = localStorage.getItem('astrara_token')
                            if (!token) { toast.error('Faca login para salvar'); return }
                            try {
                              let form: Record<string, unknown> = {}
                              try {
                                const embedded = (result as ChartResponse & { form?: Record<string, unknown> })?.form
                                const stored = sessionStorage.getItem('astrara_last_form')
                                form = embedded || (stored ? JSON.parse(stored) : {})
                              } catch { form = {} }
                              // Never save a chart without its birth data — that
                              // creates a "Meu Mapa, 2000-01-01, no city" record
                              if (!form.year || !form.city) {
                                toast.error('Dados de nascimento nao encontrados. Recalcule o mapa antes de salvar.')
                                return
                              }
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
                                  houses_json: result?.houses || [],
                                  aspects_json: result?.aspects || [],
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
                        onClick={async () => {
                          const svgEl = document.querySelector('.chart-wheel-svg') as SVGSVGElement
                          if (!svgEl) { toast.error('Mandala nao encontrada'); return }
                          const canvas = document.createElement('canvas')
                          canvas.width = 1200; canvas.height = 1200
                          const ctx = canvas.getContext('2d')
                          if (!ctx) return
                          ctx.fillStyle = '#0A0A0F'
                          ctx.fillRect(0, 0, 1200, 1200)
                          const img = new Image()
                          img.onload = async () => {
                            ctx.drawImage(img, 0, 0, 1200, 1200)
                            const dataUrl = canvas.toDataURL('image/jpeg', 0.95)
                            const { downloadDataUrl } = await import('@/lib/download')
                            await downloadDataUrl(dataUrl, 'astrara-mandala.jpg')
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
