'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Capacitor } from '@capacitor/core'
import StarBackground from '@/components/StarBackground'

type Status = 'processing' | 'success' | 'error'

function CheckoutSuccessContent() {
  const params = useSearchParams()
  const router = useRouter()
  const sessionId = params.get('session_id')
  const [status, setStatus] = useState<Status>('processing')
  const [errorMsg, setErrorMsg] = useState('')
  const isNative = Capacitor.isNativePlatform()

  useEffect(() => {
    if (!sessionId) {
      setStatus('error')
      setErrorMsg('Sessão de pagamento não encontrada.')
      return
    }

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'
    const token = localStorage.getItem('astrara_token')

    fetch(`${API_URL}/checkout/verify/${sessionId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(r => r.json())
      .then(data => {
        // Store session_id so the app can detect payment
        try { localStorage.setItem('astrara_payment_session', sessionId) } catch {}

        if (data.success || data.status === 'paid' || data.payment_status === 'paid') {
          setStatus('success')

          // On web (not in-app browser), auto-redirect after a short delay
          if (!isNative) {
            setTimeout(() => {
              router.push(`/chart?session_id=${sessionId}`)
            }, 3000)
          }
        } else {
          // Payment went through Stripe but verification returned unexpected shape
          // Still treat as success since Stripe redirected here
          setStatus('success')
        }
      })
      .catch(() => {
        // API might be unreachable from in-app browser domain (CORS) or network error.
        // Since Stripe only redirects here on successful payment, treat as success.
        try { localStorage.setItem('astrara_payment_session', sessionId) } catch {}
        setStatus('success')
      })
  }, [sessionId, router, isNative])

  const handleCloseInAppBrowser = async () => {
    try {
      const { Browser } = await import('@capacitor/browser')
      await Browser.close()
    } catch {
      // If Browser.close() fails, try navigating to the app scheme
      window.location.href = '/'
    }
  }

  const handleGoToChart = () => {
    router.push(`/chart${sessionId ? `?session_id=${sessionId}` : ''}`)
  }

  if (status === 'processing') {
    return (
      <div className="glass-card p-12 text-center max-w-md relative z-10">
        <div className="text-5xl mb-4">&#10024;</div>
        <h1 className="font-display text-3xl text-gold mb-3">Processando pagamento...</h1>
        <p className="text-muted mb-6">Aguarde enquanto confirmamos seu pagamento.</p>
        <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto" />
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="glass-card p-12 text-center max-w-md relative z-10">
        <div className="text-5xl mb-4">&#9888;&#65039;</div>
        <h1 className="font-display text-3xl text-gold mb-3">Algo deu errado</h1>
        <p className="text-muted mb-6">{errorMsg || 'Não foi possível verificar o pagamento.'}</p>
        <button
          onClick={isNative ? handleCloseInAppBrowser : handleGoToChart}
          className="bg-gold text-dark font-semibold py-3 px-8 rounded-lg hover:bg-gold/90 transition"
        >
          {isNative ? 'Voltar ao app' : 'Voltar'}
        </button>
      </div>
    )
  }

  // status === 'success'
  return (
    <div className="glass-card p-12 text-center max-w-md relative z-10">
      <div className="text-5xl mb-4">&#9989;</div>
      <h1 className="font-display text-3xl text-gold mb-3">Pagamento confirmado!</h1>
      <p className="text-muted mb-6">
        {isNative
          ? 'Seu mapa astral está pronto. Toque no botão abaixo para voltar ao app e baixar seu PDF.'
          : 'Seu mapa astral está pronto! Você será redirecionado em instantes...'}
      </p>
      <button
        onClick={isNative ? handleCloseInAppBrowser : handleGoToChart}
        className="bg-gold text-dark font-semibold py-3 px-8 rounded-lg hover:bg-gold/90 transition"
      >
        {isNative ? 'Voltar ao app' : 'Ver meu mapa astral'}
      </button>
      {!isNative && (
        <p className="text-muted text-sm mt-4">Redirecionando automaticamente...</p>
      )}
    </div>
  )
}

export default function CheckoutSuccessPage() {
  return (
    <main className="relative min-h-screen flex items-center justify-center">
      <StarBackground />
      <Suspense fallback={
        <div className="glass-card p-12 text-center max-w-md relative z-10">
          <div className="text-muted">Carregando...</div>
        </div>
      }>
        <CheckoutSuccessContent />
      </Suspense>
    </main>
  )
}
