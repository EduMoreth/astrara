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

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  viewportFit: 'cover' as const,
}

export const metadata: Metadata = {
  metadataBase: new URL('https://www.astrara.online'),
  title: 'Astrara — O cosmos, decifrado.',
  description: 'Calcule seu mapa astral gratuitamente com precisao profissional. Interpretacoes profundas com inteligencia artificial e sinastria de casal.',
  keywords: 'mapa astral, astrologia, mapa natal, horoscopo, signos, mapa astrologico, sinastria, compatibilidade de signos',
  alternates: { canonical: '/' },
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
      <body className="font-sans overflow-x-hidden">
        {/* Structured data for Google + AI crawlers */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@graph': [
                {
                  '@type': 'WebSite',
                  '@id': 'https://www.astrara.online/#website',
                  url: 'https://www.astrara.online',
                  name: 'Astrara',
                  description: 'Mapa astral gratuito com precisao profissional, interpretacoes por IA e sinastria de casal.',
                  inLanguage: 'pt-BR',
                },
                {
                  '@type': 'Organization',
                  '@id': 'https://www.astrara.online/#organization',
                  name: 'Astrara',
                  url: 'https://www.astrara.online',
                  email: 'suporte@astrara.online',
                },
                {
                  '@type': 'WebApplication',
                  name: 'Astrara — Mapa Astral',
                  url: 'https://www.astrara.online/chart',
                  applicationCategory: 'LifestyleApplication',
                  operatingSystem: 'Web',
                  offers: { '@type': 'Offer', price: '0', priceCurrency: 'BRL' },
                  description: 'Calculo gratuito de mapa astral com posicoes planetarias, casas e aspectos.',
                  inLanguage: 'pt-BR',
                },
              ],
            }),
          }}
        />
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
