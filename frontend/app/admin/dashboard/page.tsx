'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getStats, getUsers, AdminUser } from '@/lib/admin-api'

function StatCard({ icon, label, value, delta, color }: { icon: string; label: string; value: string; delta?: string; color?: string }) {
  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{icon}</span>
        <span className="text-muted text-xs uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-2xl font-display font-semibold ${color || 'text-stardust'}`}>{value}</div>
      {delta && <div className="text-gold text-xs mt-1">{delta}</div>}
    </div>
  )
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Record<string, number> | null>(null)
  const [recentUsers, setRecentUsers] = useState<AdminUser[]>([])
  const [loadError, setLoadError] = useState(false)

  useEffect(() => {
    getStats().then(setStats).catch(() => setLoadError(true))
    getUsers(1, 10).then(data => setRecentUsers(data.users ?? [])).catch(() => {})
  }, [])

  if (loadError && !stats) return (
    <div className="text-muted p-8">
      Nao foi possivel carregar o dashboard. Tente recarregar a pagina.
    </div>
  )
  if (!stats) return <div className="text-muted p-8">Carregando dashboard...</div>

  const fmt = (cents: number) => `R$ ${(cents / 100).toFixed(2).replace('.', ',')}`

  return (
    <div className="space-y-8">
      <h2 className="font-display text-2xl text-stardust">Dashboard</h2>

      {/* Row 1: Main KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          icon="👥"
          label="Usuarios"
          value={String(stats.total_users)}
          delta={`+${stats.users_today} hoje`}
        />
        <StatCard
          icon="🔮"
          label="Mapas gerados"
          value={String(stats.total_generations || 0)}
          delta={`+${stats.generations_today || 0} hoje`}
        />
        <StatCard
          icon="💰"
          label="Receita do mes"
          value={fmt(stats.monthly_revenue || 0)}
          color="text-gold"
        />
        <StatCard
          icon="⭐"
          label="Creditos em circulacao"
          value={String(stats.credits_circulation || 0)}
          delta={`${stats.credits_sold || 0} vendidos / ${stats.credits_used || 0} usados`}
        />
      </div>

      {/* Row 2: Secondary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <StatCard
          icon="💾"
          label="Mapas salvos"
          value={String(stats.total_saved_charts || 0)}
        />
        <StatCard
          icon="🎫"
          label="Tickets abertos"
          value={String(stats.open_tickets || 0)}
          color={stats.open_tickets > 0 ? 'text-[#F39C12]' : 'text-[#2ECC71]'}
        />
        <StatCard
          icon="📊"
          label="Taxa de conversao"
          value={stats.total_users > 0 ? `${((stats.credits_sold || 0) / stats.total_users * 100).toFixed(1)}%` : '0%'}
          delta="creditos comprados / usuarios"
        />
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Link href="/admin/users" className="glass-card p-4 text-center hover:border-gold/30 transition-colors">
          <span className="text-2xl block mb-1">👥</span>
          <span className="text-stardust text-sm">Usuarios</span>
        </Link>
        <Link href="/admin/tickets" className="glass-card p-4 text-center hover:border-gold/30 transition-colors">
          <span className="text-2xl block mb-1">🎫</span>
          <span className="text-stardust text-sm">Tickets</span>
          {(stats.open_tickets || 0) > 0 && (
            <span className="ml-1 text-xs bg-[#F39C12]/20 text-[#F39C12] px-1.5 py-0.5 rounded-full">{stats.open_tickets}</span>
          )}
        </Link>
        <Link href="/admin/reports" className="glass-card p-4 text-center hover:border-gold/30 transition-colors">
          <span className="text-2xl block mb-1">📊</span>
          <span className="text-stardust text-sm">Relatorios</span>
        </Link>
        <Link href="/admin/products" className="glass-card p-4 text-center hover:border-gold/30 transition-colors">
          <span className="text-2xl block mb-1">📦</span>
          <span className="text-stardust text-sm">Produtos</span>
        </Link>
      </div>

      {/* Recent users */}
      <div className="glass-card p-4 sm:p-6 overflow-x-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-stardust text-sm font-medium">Ultimos usuarios</h3>
          <Link href="/admin/users" className="text-gold text-xs hover:underline">Ver todos →</Link>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-gold/10">
              {['Nome', 'Email', 'Plano', 'Status', 'Cadastro'].map(h => (
                <th key={h} className="text-left text-xs text-muted font-normal px-3 py-2">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {recentUsers.map((u, i) => (
              <tr key={i} className="border-b border-white/[0.03]">
                <td className="px-3 py-2 text-stardust text-sm">{u.name}</td>
                <td className="px-3 py-2 text-muted text-xs">{u.email}</td>
                <td className="px-3 py-2"><span className="text-xs bg-gold/10 text-gold px-1.5 py-0.5 rounded-full">{u.plan}</span></td>
                <td className="px-3 py-2"><span className={`text-xs px-1.5 py-0.5 rounded-full ${u.status === 'active' ? 'bg-[#2ECC71]/20 text-[#2ECC71]' : 'bg-[#E74C3C]/20 text-[#E74C3C]'}`}>{u.status}</span></td>
                <td className="px-3 py-2 text-muted text-xs">{new Date(u.created_at).toLocaleDateString('pt-BR')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
