'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

function getAdminHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
}

interface Report {
  total_revenue: number
  total_refunded: number
  net_revenue: number
  refund_rate: number
  total_purchases: number
  total_refunds: number
  stripe_monthly: number
  stripe_yearly: number
  monthly_breakdown: Array<{ month: string; revenue: number; transactions: number }>
  top_products: Array<{ name: string; sales: number; revenue: number }>
}

export default function AdminReportsPage() {
  const [report, setReport] = useState<Report | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/admin/api/reports/financial`, { headers: getAdminHeaders() })
      .then(r => r.json())
      .then(setReport)
      .catch(() => toast.error('Erro ao carregar relatorio'))
  }, [])

  if (!report) return <div className="text-muted">Carregando relatorio financeiro...</div>

  const fmt = (cents: number) => `R$ ${(cents / 100).toFixed(2).replace('.', ',')}`

  return (
    <div className="space-y-8">
      <h2 className="font-display text-2xl text-stardust">Relatorio Financeiro</h2>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Receita total</div>
          <div className="text-2xl text-gold font-display">{fmt(report.total_revenue)}</div>
        </div>
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Total reembolsado</div>
          <div className="text-2xl text-[#E74C3C] font-display">{fmt(report.total_refunded)}</div>
        </div>
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Receita liquida</div>
          <div className="text-2xl text-[#2ECC71] font-display">{fmt(report.net_revenue)}</div>
        </div>
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Taxa de churn</div>
          <div className="text-2xl text-stardust font-display">{report.refund_rate}%</div>
          <div className="text-muted text-[10px] mt-1">{report.total_refunds} de {report.total_purchases} compras</div>
        </div>
      </div>

      {/* Stripe */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Stripe — Receita do mes</div>
          <div className="text-xl text-gold font-display">{fmt(report.stripe_monthly)}</div>
        </div>
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Stripe — Receita do ano</div>
          <div className="text-xl text-stardust font-display">{fmt(report.stripe_yearly)}</div>
        </div>
      </div>

      {/* Monthly breakdown */}
      <div className="glass-card p-6">
        <h3 className="text-stardust text-sm font-medium mb-4">Receita mensal (ultimos 12 meses)</h3>
        {report.monthly_breakdown.length > 0 ? (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gold/10">
                <th className="text-left text-xs text-muted font-normal px-4 py-2">Mes</th>
                <th className="text-right text-xs text-muted font-normal px-4 py-2">Receita</th>
                <th className="text-right text-xs text-muted font-normal px-4 py-2">Transacoes</th>
              </tr>
            </thead>
            <tbody>
              {report.monthly_breakdown.map(m => (
                <tr key={m.month} className="border-b border-white/[0.03]">
                  <td className="px-4 py-2 text-stardust text-sm">{m.month}</td>
                  <td className="px-4 py-2 text-gold text-sm text-right">{fmt(m.revenue)}</td>
                  <td className="px-4 py-2 text-muted text-sm text-right">{m.transactions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-muted text-sm">Nenhuma transacao nos ultimos 12 meses</p>
        )}
      </div>

      {/* Top products */}
      <div className="glass-card p-6">
        <h3 className="text-stardust text-sm font-medium mb-4">Produtos mais vendidos</h3>
        {report.top_products.length > 0 ? (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gold/10">
                <th className="text-left text-xs text-muted font-normal px-4 py-2">Produto</th>
                <th className="text-right text-xs text-muted font-normal px-4 py-2">Vendas</th>
                <th className="text-right text-xs text-muted font-normal px-4 py-2">Receita</th>
              </tr>
            </thead>
            <tbody>
              {report.top_products.map((p, i) => (
                <tr key={i} className="border-b border-white/[0.03]">
                  <td className="px-4 py-2 text-stardust text-sm">{p.name}</td>
                  <td className="px-4 py-2 text-muted text-sm text-right">{p.sales}</td>
                  <td className="px-4 py-2 text-gold text-sm text-right">{fmt(p.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-muted text-sm">Nenhuma venda registrada</p>
        )}
      </div>
    </div>
  )
}
