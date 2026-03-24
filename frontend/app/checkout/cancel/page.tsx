'use client'

import Link from 'next/link'
import StarBackground from '@/components/StarBackground'

export default function CheckoutCancelPage() {
  return (
    <main className="relative min-h-screen flex items-center justify-center">
      <StarBackground />
      <div className="glass-card p-12 text-center max-w-md relative z-10">
        <div className="text-5xl mb-4">🌙</div>
        <h1 className="font-display text-3xl text-stardust mb-3">Pagamento cancelado</h1>
        <p className="text-muted mb-6">Voce pode tentar novamente quando quiser.</p>
        <Link href="/chart" className="btn-primary text-sm">Voltar ao mapa</Link>
      </div>
    </main>
  )
}
