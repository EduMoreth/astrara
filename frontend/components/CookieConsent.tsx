'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function CookieConsent() {
  const [show, setShow] = useState(false)

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null
    // Don't show cookie consent in native apps (no cookies used)
    import('@capacitor/core').then(({ Capacitor }) => {
      if (Capacitor.isNativePlatform()) return
      const consent = localStorage.getItem('astrara_cookie_consent')
      if (!consent) {
        timer = setTimeout(() => setShow(true), 1000)
      }
    })
    return () => { if (timer) clearTimeout(timer) }
  }, [])

  function accept() {
    localStorage.setItem('astrara_cookie_consent', 'accepted')
    localStorage.setItem('astrara_cookie_consent_date', new Date().toISOString())
    setShow(false)
  }

  function reject() {
    localStorage.setItem('astrara_cookie_consent', 'rejected')
    localStorage.setItem('astrara_cookie_consent_date', new Date().toISOString())
    setShow(false)
  }

  if (!show) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[100] p-4">
      <div className="max-w-2xl mx-auto glass-card p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex-1">
          <p className="text-stardust text-sm">
            Utilizamos cookies essenciais para o funcionamento do site.
            Ao continuar, voce concorda com nossa{' '}
            <Link href="/privacidade" className="text-gold hover:underline">Politica de Privacidade</Link>.
          </p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <button onClick={reject} className="px-4 py-2 text-xs text-muted border border-gold/20 rounded-full hover:border-gold/40">
            Rejeitar
          </button>
          <button onClick={accept} className="px-4 py-2 text-xs bg-gold text-cosmos rounded-full font-medium hover:bg-gold/90">
            Aceitar
          </button>
        </div>
      </div>
    </div>
  )
}
