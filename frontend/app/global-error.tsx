'use client'

import { useEffect } from 'react'

/**
 * Global error boundary — catches errors thrown in the root layout itself,
 * where the normal app/error.tsx boundary and app styles are unavailable.
 * Must render its own <html>/<body>. Styles are inline for that reason.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Global error boundary caught:', error)
  }, [error])

  return (
    <html lang="pt-BR">
      <body
        style={{
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0A0A0F',
          color: '#F0EDE8',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          padding: '1rem',
        }}
      >
        <div style={{ textAlign: 'center', maxWidth: 420 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>&#10024;</div>
          <h1 style={{ color: '#C9A96E', fontSize: 26, marginBottom: 12 }}>
            Algo deu errado
          </h1>
          <p style={{ color: '#8B8A9B', marginBottom: 28, lineHeight: 1.5 }}>
            Ocorreu um erro inesperado. Se voce acabou de fazer um pagamento, seu
            credito foi registrado e continua disponivel na sua conta.
          </p>
          <button
            onClick={() => reset()}
            style={{
              background: '#C9A96E',
              color: '#0A0A0F',
              fontWeight: 600,
              padding: '12px 32px',
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Tentar novamente
          </button>
        </div>
      </body>
    </html>
  )
}
