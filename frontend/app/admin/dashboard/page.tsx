'use client'

import { useEffect, useState } from 'react'
import { getStats, getUsersDaily, getRevenueDaily } from '@/lib/admin-api'

function StatCard({ icon, label, value, delta }: { icon: string; label: string; value: string; delta?: string }) {
  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-2xl">{icon}</span>
        <span className="text-muted text-sm">{label}</span>
      </div>
      <div className="text-3xl font-display font-semibold text-stardust">{value}</div>
      {delta && <div className="text-gold text-xs mt-1">{delta}</div>}
    </div>
  )
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Record<string, number> | null>(null)

  useEffect(() => {
    getStats().then(setStats).catch(console.error)
  }, [])

  if (!stats) return <div className="text-muted">Carregando...</div>

  return (
    <div className="space-y-8">
      <h2 className="font-display text-2xl text-stardust">Dashboard</h2>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon="👥"
          label="Total usuarios"
          value={String(stats.total_users)}
          delta={`+${stats.users_today} hoje`}
        />
        <StatCard
          icon="🔮"
          label="Mapas gerados"
          value={String(stats.total_charts)}
          delta={`+${stats.charts_today} hoje`}
        />
        <StatCard
          icon="💰"
          label="Receita do mes"
          value={`R$ ${(stats.monthly_revenue / 100).toFixed(2)}`}
        />
        <StatCard
          icon="⭐"
          label="Creditos em circulacao"
          value={String(stats.credits_circulation)}
          delta={`${stats.credits_sold} vendidos / ${stats.credits_used} usados`}
        />
      </div>

      {/* Charts would go here with recharts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-stardust text-sm font-medium mb-4">Novos usuarios (30 dias)</h3>
          <div className="text-muted text-xs">Grafico disponivel com recharts</div>
        </div>
        <div className="glass-card p-6">
          <h3 className="text-stardust text-sm font-medium mb-4">Receita diaria (30 dias)</h3>
          <div className="text-muted text-xs">Grafico disponivel com recharts</div>
        </div>
      </div>
    </div>
  )
}
