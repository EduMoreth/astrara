'use client'

import { Suspense, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import StarBackground from '@/components/StarBackground'

function CheckoutSuccessContent() {
  const params = useSearchParams()
  const router = useRouter()
  const sessionId = params.get('session_id')

  useEffect(() => {
    if (!sessionId) return

    // Verify payment first
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'
    const token = localStorage.getItem('astrara_token')

    fetch(`${API_URL}/checkout/verify/${sessionId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          // Redirect back to chart page with session_id so it knows payment was made
          // The chart result is preserved in sessionStorage
          router.push(`/chart?session_id=${sessionId}`)
        }
      })
      .catch(() => {
        router.push('/chart')
      })
  }, [sessionId, router])

  return (
    <div className="glass-card p-12 text-center max-w-md relative z-10">
      <div className="text-5xl mb-4">✨</div>
      <h1 className="font-display text-3xl text-gold mb-3">Processando pagamento...</h1>
      <p className="text-muted mb-6">Aguarde, voce sera redirecionado para baixar seu PDF.</p>
      <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto" />
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
