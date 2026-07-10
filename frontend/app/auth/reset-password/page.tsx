'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

function ResetPasswordForm() {
  const params = useSearchParams()
  const token = params.get('token') || ''
  const forced = params.get('forced') === 'true'
  const forcedEmail = params.get('email') || ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)
  const [forcedEmailSent, setForcedEmailSent] = useState(false)

  // Forced-reset flow (admin flagged the account): there is no token yet, so
  // automatically request a reset link for the email and tell the user.
  useEffect(() => {
    if (!token && forced && forcedEmail && !forcedEmailSent) {
      fetch(`${API_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forcedEmail }),
      })
        .catch(() => {})
        .finally(() => setForcedEmailSent(true))
    }
  }, [token, forced, forcedEmail, forcedEmailSent])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password !== confirm) { toast.error('As senhas nao coincidem'); return }
    if (password.length < 8) { toast.error('Senha deve ter pelo menos 8 caracteres'); return }

    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Erro')
      setDone(true)
      toast.success('Senha redefinida com sucesso!')
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao redefinir senha')
    } finally {
      setLoading(false)
    }
  }

  if (!token && forced) {
    return (
      <div className="text-center">
        <div className="text-4xl mb-4">&#128231;</div>
        <p className="text-stardust mb-2">Redefinicao de senha necessaria</p>
        <p className="text-muted text-sm mb-6">
          {forcedEmailSent
            ? `Enviamos um link de redefinicao para ${forcedEmail}. Verifique sua caixa de entrada (e o spam).`
            : 'Enviando link de redefinicao para o seu email...'}
        </p>
        <Link href="/auth/login" className="text-gold hover:underline text-sm">Voltar ao login</Link>
      </div>
    )
  }

  if (!token) {
    return (
      <div className="text-center">
        <p className="text-[#E74C3C] mb-4">Link invalido. Solicite um novo link de recuperacao.</p>
        <Link href="/auth/forgot-password" className="text-gold hover:underline">Solicitar novo link</Link>
      </div>
    )
  }

  if (done) {
    return (
      <div className="text-center">
        <div className="text-4xl mb-4">✅</div>
        <p className="text-stardust mb-2">Senha redefinida!</p>
        <p className="text-muted text-sm mb-6">Voce ja pode fazer login com sua nova senha.</p>
        <Link href="/auth/login" className="btn-primary text-sm">Ir para o login</Link>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-stardust/70 text-sm mb-2">Nova senha</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)}
          className="input-field w-full" placeholder="Minimo 8 caracteres" required />
      </div>
      <div>
        <label className="block text-stardust/70 text-sm mb-2">Confirmar nova senha</label>
        <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
          className="input-field w-full" placeholder="Repita a senha" required />
      </div>
      <button type="submit" disabled={loading} className="btn-primary w-full">
        {loading ? 'Salvando...' : 'Redefinir senha'}
      </button>
    </form>
  )
}

export default function ResetPasswordPage() {
  return (
    <main className="relative min-h-screen flex items-center justify-center">
      <StarBackground />
      <div className="glass-card p-10 w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <Link href="/" className="font-display text-3xl font-semibold text-gradient-gold">Astrara</Link>
          <p className="text-muted text-sm mt-2">Redefinir senha</p>
        </div>
        <Suspense fallback={<div className="text-muted text-center">Carregando...</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </main>
  )
}
