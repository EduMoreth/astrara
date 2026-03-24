'use client'

import { useState } from 'react'
import Link from 'next/link'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await fetch(`${API_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      setSent(true)
    } catch {
      toast.error('Erro ao enviar. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="relative min-h-screen flex items-center justify-center">
      <StarBackground />
      <div className="glass-card p-10 w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <Link href="/" className="font-display text-3xl font-semibold text-gradient-gold">Astrara</Link>
          <p className="text-muted text-sm mt-2">Recuperar senha</p>
        </div>

        {sent ? (
          <div className="text-center">
            <div className="text-4xl mb-4">📧</div>
            <p className="text-stardust mb-2">Email enviado!</p>
            <p className="text-muted text-sm mb-6">
              Se o email estiver cadastrado, voce recebera um link para redefinir sua senha. Verifique tambem a pasta de spam.
            </p>
            <Link href="/auth/login" className="text-gold text-sm hover:underline">Voltar ao login</Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-stardust/70 text-sm mb-2">Email da sua conta</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="input-field w-full"
                placeholder="seu@email.com"
                required
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Enviando...' : 'Enviar link de recuperacao'}
            </button>
            <p className="text-center text-sm text-muted">
              <Link href="/auth/login" className="text-gold hover:underline">Voltar ao login</Link>
            </p>
          </form>
        )}
      </div>
    </main>
  )
}
