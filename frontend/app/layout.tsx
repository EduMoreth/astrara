import type { Metadata } from 'next'
import { Inter, Cormorant_Garamond } from 'next/font/google'
import { Toaster } from 'sonner'
import CookieConsent from '@/components/CookieConsent'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

const cormorant = Cormorant_Garamond({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-cormorant',
})

export const metadata: Metadata = {
  title: 'Astrara — O cosmos, decifrado.',
  description: 'Calcule seu mapa astral gratuitamente com precisao profissional. Interpretacoes profundas com inteligencia artificial.',
  keywords: 'mapa astral, astrologia, mapa natal, horoscopo, signos, mapa astrologico',
  openGraph: {
    title: 'Astrara — O cosmos, decifrado.',
    description: 'Calcule seu mapa astral gratuitamente. Interpretacoes com IA.',
    url: 'https://www.astrara.online',
    siteName: 'Astrara',
    type: 'website',
    locale: 'pt_BR',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Astrara — O cosmos, decifrado.',
    description: 'Calcule seu mapa astral gratuitamente. Interpretacoes com IA.',
  },
  robots: { index: true, follow: true },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${cormorant.variable}`}>
      <body className="font-sans">
        {children}
        <CookieConsent />
        <Toaster
          theme="dark"
          position="top-right"
          toastOptions={{
            style: {
              background: 'rgba(18, 18, 26, 0.9)',
              border: '1px solid rgba(201, 169, 110, 0.2)',
              color: '#F0EDE8',
              backdropFilter: 'blur(20px)',
            },
          }}
        />
      </body>
    </html>
  )
}
