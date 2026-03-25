'use client'

import { usePathname, useRouter } from 'next/navigation'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { isAdminLoggedIn, clearAdminToken } from '@/lib/admin-api'

const NAV_ITEMS = [
  { href: '/admin/dashboard', label: 'Dashboard', icon: '✦' },
  { href: '/admin/users', label: 'Usuarios', icon: '👥' },
  { href: '/admin/products', label: 'Produtos', icon: '📦' },
  { href: '/admin/transactions', label: 'Transacoes', icon: '💳' },
  { href: '/admin/tickets', label: 'Tickets', icon: '🎫' },
  { href: '/admin/reports', label: 'Relatorios', icon: '📊' },
  { href: '/admin/charts', label: 'Mapas', icon: '🔮' },
  { href: '/admin/instagram', label: 'Instagram', icon: '📸' },
  { href: '/admin/config', label: 'Config', icon: '⚙️' },
  { href: '/admin/logs', label: 'Logs', icon: '📋' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [ready, setReady] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const isLoginPage = pathname === '/admin/login'

  useEffect(() => {
    if (!isLoginPage && !isAdminLoggedIn()) {
      router.push('/admin/login')
    } else {
      setReady(true)
    }
  }, [isLoginPage, router])

  // Close mobile menu on navigation
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [pathname])

  if (isLoginPage) return <>{children}</>
  if (!ready) return null

  return (
    <div className="flex h-screen bg-cosmos">
      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - hidden on mobile, shown on lg+ */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-60 bg-[#0D0D14] border-r border-gold/10 flex flex-col
        transform transition-transform duration-200 ease-in-out
        lg:relative lg:translate-x-0
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="px-5 py-5 border-b border-gold/10 flex items-center justify-between">
          <Link href="/admin/dashboard" className="font-display text-lg sm:text-xl text-gradient-gold font-semibold">
            ✦ Astrara Admin
          </Link>
          {/* Close button on mobile */}
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="lg:hidden text-muted hover:text-stardust text-xl"
          >
            ✕
          </button>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const active = pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-5 py-3 text-sm transition-colors ${
                  active
                    ? 'text-gold border-l-2 border-gold bg-gold/5'
                    : 'text-muted hover:text-stardust hover:bg-surface/50 border-l-2 border-transparent'
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="px-5 py-4 border-t border-gold/10">
          <button
            onClick={() => { clearAdminToken(); router.push('/admin/login') }}
            className="text-muted hover:text-red-400 text-sm transition-colors"
          >
            Sair
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto w-full">
        <header className="h-14 sm:h-16 border-b border-gold/10 flex items-center justify-between px-4 sm:px-8 bg-[#0D0D14]/80 backdrop-blur-sm sticky top-0 z-10">
          <div className="flex items-center gap-3">
            {/* Hamburger menu - mobile only */}
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden text-stardust text-xl p-1"
            >
              ☰
            </button>
            <h1 className="text-stardust text-sm font-medium">
              {NAV_ITEMS.find(i => pathname.startsWith(i.href))?.label || 'Admin'}
            </h1>
          </div>
          <span className="text-muted text-xs hidden sm:inline">Admin</span>
        </header>
        <div className="p-4 sm:p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
