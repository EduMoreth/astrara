'use client'

import { useState, FormEvent } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'
import { login as apiLogin } from '@/lib/api'
import { setToken } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)

    try {
      const res = await apiLogin(email, password)
      if (res.force_password_reset) {
        toast.error(res.message || 'Voce precisa redefinir sua senha.')
        router.push('/auth/reset-password?forced=true&email=' + encodeURIComponent(email))
        return
      }
      setToken(res.access_token)
      toast.success('Bem-vindo de volta!')
      router.push('/dashboard')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao entrar'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="relative min-h-screen flex items-center justify-center">
      <StarBackground />

      <motion.div
        className="relative z-10 w-full max-w-md mx-6"
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
            Entrar
          </h1>

          <form onSubmit={handleSubmit} className="space-y-5">
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
                placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Link href="/auth/forgot-password" className="text-gold/60 hover:text-gold text-xs mt-2 inline-block transition-colors">
                Esqueci minha senha
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-2 disabled:opacity-50"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          <p className="text-center text-sm text-muted mt-6">
            Nao tem conta?{' '}
            <Link href="/auth/register" className="text-gold hover:text-gold/80 transition-colors">
              Criar gratis
            </Link>
          </p>
        </div>
      </motion.div>
    </main>
  )
}
