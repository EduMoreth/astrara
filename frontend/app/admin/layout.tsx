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
  { href: '/admin/charts', label: 'Mapas', icon: '🔮' },
  { href: '/admin/config', label: 'Config', icon: '⚙️' },
  { href: '/admin/logs', label: 'Logs', icon: '📋' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [ready, setReady] = useState(false)

  const isLoginPage = pathname === '/admin/login'

  useEffect(() => {
    if (!isLoginPage && !isAdminLoggedIn()) {
      router.push('/admin/login')
    } else {
      setReady(true)
    }
  }, [isLoginPage, router])

  if (isLoginPage) return <>{children}</>
  if (!ready) return null

  return (
    <div className="flex h-screen bg-cosmos">
      {/* Sidebar */}
      <aside className="w-60 bg-[#0D0D14] border-r border-gold/10 flex flex-col">
        <div className="px-5 py-5 border-b border-gold/10">
          <Link href="/admin/dashboard" className="font-display text-xl text-gradient-gold font-semibold">
            ✦ Astrara Admin
          </Link>
        </div>
        <nav className="flex-1 py-4">
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
      <main className="flex-1 overflow-auto">
        <header className="h-16 border-b border-gold/10 flex items-center justify-between px-8 bg-[#0D0D14]/80 backdrop-blur-sm sticky top-0 z-10">
          <h1 className="text-stardust text-sm font-medium">
            {NAV_ITEMS.find(i => pathname.startsWith(i.href))?.label || 'Admin'}
          </h1>
          <span className="text-muted text-xs">Admin</span>
        </header>
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
