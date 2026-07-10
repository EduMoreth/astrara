'use client'

import { useEffect } from 'react'

/**
 * Route-level error boundary. Catches client-side exceptions during render and
 * shows a friendly recovery UI instead of the raw "Application error" screen.
 *
 * Stale chunk errors (common right after a new deploy, when the browser still
 * holds cached HTML that references renamed JS chunks) are auto-recovered with a
 * one-time hard reload, guarded so we never loop.
 */
function isChunkLoadError(error: Error): boolean {
  const msg = `${error?.name || ''} ${error?.message || ''}`
  return (
    /ChunkLoadError/i.test(msg) ||
    /Loading chunk [\w-]+ failed/i.test(msg) ||
    /Failed to fetch dynamically imported module/i.test(msg) ||
    /error loading dynamically imported module/i.test(msg)
  )
}

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log so the real error is visible in the console for diagnosis.
    console.error('App error boundary caught:', error)

    if (isChunkLoadError(error) && typeof window !== 'undefined') {
      const KEY = 'astrara_chunk_reload'
      // Only auto-reload once per session to avoid an infinite reload loop.
      if (!sessionStorage.getItem(KEY)) {
        sessionStorage.setItem(KEY, '1')
        window.location.reload()
      }
    }
  }, [error])

  return (
    <main className="relative min-h-screen flex items-center justify-center px-4">
      <div className="glass-card p-10 sm:p-12 text-center max-w-md relative z-10">
        <div className="text-5xl mb-4">&#10024;</div>
        <h1 className="font-display text-2xl sm:text-3xl text-gold mb-3">
          Algo deu errado
        </h1>
        <p className="text-muted mb-8 text-sm sm:text-base">
          Ocorreu um erro inesperado ao carregar esta pagina. Isso costuma ser
          temporario. Se voce acabou de fazer um pagamento, fique tranquilo: seu
          credito foi registrado e continua disponivel em &quot;Meus mapas&quot;.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => reset()}
            className="bg-gold text-dark font-semibold py-3 px-8 rounded-lg hover:bg-gold/90 transition"
          >
            Tentar novamente
          </button>
          <button
            onClick={() => {
              if (typeof window !== 'undefined') window.location.href = '/dashboard'
            }}
            className="border border-gold/30 text-stardust font-semibold py-3 px-8 rounded-lg hover:bg-gold/10 transition"
          >
            Ir para Meus mapas
          </button>
        </div>
      </div>
    </main>
  )
}
