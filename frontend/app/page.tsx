'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import StarBackground from '@/components/StarBackground'

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.7, ease: [0.22, 1, 0.36, 1] },
  }),
}

const features = [
  {
    icon: '\uD83C\uDF19',
    title: 'C\u00e1lculo Preciso',
    desc: 'Swiss Ephemeris, o mesmo motor usado pelos melhores astr\u00f3logos do mundo.',
  },
  {
    icon: '\u2728',
    title: 'Design Celestial',
    desc: 'Sua mandala gerada em alta resolu\u00e7\u00e3o para salvar e compartilhar.',
  },
  {
    icon: '\uD83D\uDD2E',
    title: 'Interpreta\u00e7\u00e3o com IA',
    desc: 'An\u00e1lise profunda de cada planeta, casa e aspecto do seu mapa.',
  },
]

const steps = [
  'Informe data, hora e cidade de nascimento',
  'Seu mapa \u00e9 calculado instantaneamente',
  'Receba sua mandala e posi\u00e7\u00f5es astrol\u00f3gicas',
  'Desbloqueie a interpreta\u00e7\u00e3o completa com IA',
]

export default function LandingPage() {
  return (
    <main className="relative min-h-screen">
      <StarBackground />

      {/* ─── Nav ──────────────────────────────────── */}
      <nav className="relative z-10 flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-xl sm:text-2xl font-semibold text-gradient-gold">
          Astrara
        </Link>
        <div className="flex items-center gap-2 sm:gap-4">
          <Link href="/auth/login" className="text-muted hover:text-stardust transition-colors text-xs sm:text-sm">
            Entrar
          </Link>
          <Link href="/chart" className="btn-primary !text-xs sm:!text-sm !py-2 sm:!py-2.5 !px-4 sm:!px-5 !w-auto">
            Criar meu mapa
          </Link>
        </div>
      </nav>

      {/* ─── Hero ─────────────────────────────────── */}
      <section className="relative z-10 flex flex-col items-center text-center px-4 sm:px-6 pt-12 sm:pt-20 pb-16 sm:pb-32 max-w-4xl mx-auto">
        <motion.h1
          className="font-display text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-light leading-[1.1] text-stardust"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        >
          Seu mapa astral,
          <br />
          <span className="text-gradient-gold font-medium">revelado com precis&#227;o.</span>
        </motion.h1>

        <motion.p
          className="mt-4 sm:mt-6 text-base sm:text-lg text-muted max-w-xl px-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.7 }}
        >
          Calcule seu mapa natal gratuitamente.
          <br />
          Interpreta&#231;&#245;es profundas com intelig&#234;ncia artificial.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.7 }}
        >
          <Link href="/chart" className="btn-primary mt-10 text-lg">
            Descobrir meu mapa &rarr;
          </Link>
        </motion.div>

        {/* Mandala preview rotating */}
        <motion.div
          className="mt-20 relative"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7, duration: 1, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="absolute inset-0 rounded-full bg-violet/10 blur-[80px]" />
          <motion.svg
            viewBox="0 0 400 400"
            className="w-64 h-64 sm:w-80 sm:h-80 md:w-96 md:h-96"
            animate={{ rotate: 360 }}
            transition={{ duration: 120, repeat: Infinity, ease: 'linear' }}
          >
            {/* Outer ring */}
            <circle cx="200" cy="200" r="185" fill="none" stroke="rgba(201,169,110,0.2)" strokeWidth="1" />
            <circle cx="200" cy="200" r="160" fill="none" stroke="rgba(201,169,110,0.15)" strokeWidth="0.5" />
            <circle cx="200" cy="200" r="120" fill="none" stroke="rgba(123,94,167,0.2)" strokeWidth="0.5" />
            <circle cx="200" cy="200" r="80" fill="none" stroke="rgba(201,169,110,0.1)" strokeWidth="0.5" />

            {/* Sign divisions */}
            {Array.from({ length: 12 }).map((_, i) => {
              const angle = (i * 30 * Math.PI) / 180
              const x1 = 200 + 120 * Math.cos(angle)
              const y1 = 200 + 120 * Math.sin(angle)
              const x2 = 200 + 185 * Math.cos(angle)
              const y2 = 200 + 185 * Math.sin(angle)
              return (
                <line
                  key={i}
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke="rgba(201,169,110,0.12)"
                  strokeWidth="0.5"
                />
              )
            })}

            {/* Center dot */}
            <circle cx="200" cy="200" r="3" fill="rgba(201,169,110,0.5)" />

            {/* Decorative planet dots */}
            {[45, 90, 135, 200, 260, 310].map((deg, i) => {
              const r = 100 + (i % 3) * 30
              const x = 200 + r * Math.cos((deg * Math.PI) / 180)
              const y = 200 + r * Math.sin((deg * Math.PI) / 180)
              return (
                <circle
                  key={i}
                  cx={x} cy={y}
                  r={2 + (i % 2)}
                  fill={i % 2 === 0 ? 'rgba(201,169,110,0.6)' : 'rgba(123,94,167,0.6)'}
                />
              )
            })}
          </motion.svg>
        </motion.div>
      </section>

      {/* ─── Features ─────────────────────────────── */}
      <section className="relative z-10 px-6 py-24 max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              className="glass-card p-8 text-center"
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-50px' }}
              variants={fadeUp}
            >
              <span className="text-4xl block mb-4">{f.icon}</span>
              <h3 className="font-display text-xl font-semibold text-stardust mb-3">
                {f.title}
              </h3>
              <p className="text-muted text-sm leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── How it Works ─────────────────────────── */}
      <section className="relative z-10 px-6 py-24 max-w-3xl mx-auto">
        <motion.h2
          className="font-display text-3xl sm:text-4xl text-center font-light text-stardust mb-16"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Como funciona
        </motion.h2>

        <div className="relative">
          {/* Gold connector line */}
          <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-gold/40 via-gold/20 to-transparent" />

          <div className="space-y-10">
            {steps.map((step, i) => (
              <motion.div
                key={i}
                className="flex items-start gap-6 relative"
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-30px' }}
                variants={fadeUp}
              >
                <div className="w-12 h-12 rounded-full bg-surface border border-gold/30 flex items-center justify-center shrink-0 relative z-10">
                  <span className="text-gold font-display text-lg font-semibold">
                    {i + 1}
                  </span>
                </div>
                <p className="text-stardust/80 text-lg pt-2.5">{step}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────── */}
      <section className="relative z-10 px-6 py-24 text-center">
        <motion.div
          className="glass-card max-w-xl mx-auto p-12"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
        >
          <h2 className="font-display text-3xl font-light text-stardust mb-4">
            Pronto para explorar os astros?
          </h2>
          <p className="text-muted mb-8">
            Seu mapa astral gratuito em menos de 30 segundos.
          </p>
          <Link href="/chart" className="btn-primary text-lg">
            Criar meu mapa &rarr;
          </Link>
        </motion.div>
      </section>

      {/* ─── Footer ───────────────────────────────── */}
      <footer className="relative z-10 border-t border-gold/10 px-6 py-8">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="font-display text-lg font-semibold text-gradient-gold">
              Astrara
            </span>
            <span className="text-muted text-sm">O cosmos, decifrado.</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted">
            <a href="/privacidade" className="hover:text-stardust transition-colors">
              Pol&#237;tica de Privacidade
            </a>
            <span className="text-gold/20">·</span>
            <a href="/termos" className="hover:text-stardust transition-colors">
              Termos de Uso
            </a>
            <span className="text-gold/20">·</span>
            <a href="/support" className="hover:text-stardust transition-colors">
              Suporte
            </a>
          </div>
        </div>
      </footer>
    </main>
  )
}
