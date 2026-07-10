'use client'

import { useState, FormEvent } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'
import { register as apiRegister } from '@/lib/api'
import { setToken } from '@/lib/auth'

export default function RegisterPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [consent, setConsent] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (password !== confirmPassword) {
      toast.error('As senhas nao coincidem')
      return
    }

    if (password.length < 8) {
      toast.error('A senha deve ter pelo menos 8 caracteres')
      return
    }

    if (!consent) {
      toast.error('Voce precisa aceitar a Politica de Privacidade e os Termos de Uso')
      return
    }

    setLoading(true)

    try {
      const res = await apiRegister(name, email, password)
      setToken(res.access_token)
      toast.success('Conta criada com sucesso!')
      // Check if user had an intent before registering
      const intent = sessionStorage.getItem('astrara_intent')
      if (intent === 'buy_interpretation') {
        sessionStorage.removeItem('astrara_intent')
        router.push('/chart')
      } else {
        router.push('/dashboard')
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao criar conta'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="relative min-h-screen flex items-center justify-center">
      <StarBackground />

      <motion.div
        className="relative z-10 w-full max-w-md mx-6 my-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="glass-card p-8 sm:p-10">
          {/* Logo */}
          <div className="text-center mb-8">
            <Link href="/" className="font-display text-3xl font-semibold text-gradient-gold">
              Astrara
            </Link>
          </div>

          <h1 className="font-display text-2xl font-light text-stardust text-center mb-8">
            Criar conta
          </h1>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm text-muted mb-2">Nome completo</label>
              <input
                type="text"
                className="input-field"
                placeholder="Seu nome"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm text-muted mb-2">Email</label>
              <input
                type="email"
                className="input-field"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm text-muted mb-2">Senha</label>
              <input
                type="password"
                className="input-field"
                placeholder="Minimo 8 caracteres"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <div>
              <label className="block text-sm text-muted mb-2">Confirmar senha</label>
              <input
                type="password"
                className="input-field"
                placeholder="Repita a senha"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={consent}
                onChange={e => setConsent(e.target.checked)}
                className="mt-1 accent-gold w-4 h-4 flex-shrink-0"
              />
              <span className="text-xs text-muted leading-relaxed">
                Li e concordo com a{' '}
                <Link href="/privacidade" target="_blank" className="text-gold hover:underline">Politica de Privacidade</Link>
                {' '}e os{' '}
                <Link href="/termos" target="_blank" className="text-gold hover:underline">Termos de Uso</Link>.
                Autorizo o tratamento dos meus dados pessoais conforme descrito.
              </span>
            </label>

            <button
              type="submit"
              disabled={loading || !consent}
              className="btn-primary w-full mt-2 disabled:opacity-50"
            >
              {loading ? 'Criando conta...' : 'Criar conta gratis'}
            </button>
          </form>

          <p className="text-center text-sm text-muted mt-6">
            Ja tem conta?{' '}
            <Link href="/auth/login" className="text-gold hover:text-gold/80 transition-colors">
              Entrar
            </Link>
          </p>
        </div>
      </motion.div>
    </main>
  )
}
