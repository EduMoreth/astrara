'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import StarBackground from '@/components/StarBackground'

function CheckoutSuccessContent() {
  const params = useSearchParams()
  const sessionId = params.get('session_id')
  const [verified, setVerified] = useState(false)

  useEffect(() => {
    if (!sessionId) return
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'
    const token = localStorage.getItem('astrara_token')
    fetch(`${API_URL}/checkout/verify/${sessionId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(r => r.json())
      .then(data => { if (data.success) setVerified(true) })
      .catch(() => {})
  }, [sessionId])

  return (
    <div className="glass-card p-12 text-center max-w-md relative z-10">
      <div className="text-5xl mb-4">✨</div>
      <h1 className="font-display text-3xl text-gold mb-3">Pagamento confirmado!</h1>
      <p className="text-muted mb-6">
        {verified ? 'Seus creditos foram adicionados a sua conta.' : 'Verificando pagamento...'}
      </p>
      <Link href="/chart" className="btn-primary text-sm">Voltar ao mapa</Link>
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
