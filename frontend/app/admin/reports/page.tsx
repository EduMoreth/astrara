'use client'

import { useEffect, useState, useCallback } from 'react'
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
  daily_breakdown: Array<{ day: string; revenue: number; transactions: number }>
  monthly_breakdown: Array<{ month: string; revenue: number; transactions: number }>
  top_products: Array<{ name: string; sales: number; revenue: number }>
}

const PRESETS = [
  { label: 'Hoje', from: () => new Date().toISOString().slice(0, 10), to: () => new Date().toISOString().slice(0, 10) },
  { label: '7 dias', from: () => { const d = new Date(); d.setDate(d.getDate() - 7); return d.toISOString().slice(0, 10) }, to: () => new Date().toISOString().slice(0, 10) },
  { label: '30 dias', from: () => { const d = new Date(); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10) }, to: () => new Date().toISOString().slice(0, 10) },
  { label: 'Este mes', from: () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01` }, to: () => new Date().toISOString().slice(0, 10) },
  { label: 'Este ano', from: () => `${new Date().getFullYear()}-01-01`, to: () => new Date().toISOString().slice(0, 10) },
  { label: 'Ano passado', from: () => `${new Date().getFullYear() - 1}-01-01`, to: () => `${new Date().getFullYear() - 1}-12-31` },
  { label: 'Todo periodo', from: () => '', to: () => '' },
]

export default function AdminReportsPage() {
  const [report, setReport] = useState<Report | null>(null)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [activePreset, setActivePreset] = useState('Todo periodo')

  const loadReport = useCallback(() => {
    const params = new URLSearchParams()
    if (dateFrom) params.set('date_from', dateFrom)
    if (dateTo) params.set('date_to', dateTo)
    fetch(`${API_URL}/admin/api/reports/financial?${params}`, { headers: getAdminHeaders() })
      .then(r => r.json())
      .then(setReport)
      .catch(() => toast.error('Erro ao carregar'))
  }, [dateFrom, dateTo])

  useEffect(() => { loadReport() }, [loadReport])

  function applyPreset(preset: typeof PRESETS[0]) {
    setDateFrom(preset.from())
    setDateTo(preset.to())
    setActivePreset(preset.label)
  }

  if (!report) return <div className="text-muted">Carregando relatorio financeiro...</div>

  const fmt = (cents: number) => `R$ ${(cents / 100).toFixed(2).replace('.', ',')}`

  return (
    <div className="space-y-6">
      <h2 className="font-display text-2xl text-stardust">Relatorio Financeiro</h2>

      {/* Date range filter */}
      <div className="glass-card p-4">
        <div className="flex flex-wrap gap-2 mb-4">
          {PRESETS.map(p => (
            <button key={p.label} onClick={() => applyPreset(p)}
              className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
                activePreset === p.label ? 'bg-gold text-cosmos font-medium' : 'text-muted border border-gold/20 hover:border-gold/40'
              }`}>
              {p.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <div>
            <label className="text-muted text-[10px] uppercase tracking-wider block mb-1">De</label>
            <input type="date" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setActivePreset('') }}
              className="input-field text-sm py-1.5 px-3" />
          </div>
          <div>
            <label className="text-muted text-[10px] uppercase tracking-wider block mb-1">Ate</label>
            <input type="date" value={dateTo} onChange={e => { setDateTo(e.target.value); setActivePreset('') }}
              className="input-field text-sm py-1.5 px-3" />
          </div>
          {dateFrom && <span className="text-muted text-xs self-end pb-2">{dateFrom} a {dateTo || 'hoje'}</span>}
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Receita bruta</div>
          <div className="text-2xl text-gold font-display">{fmt(report.total_revenue)}</div>
          <div className="text-muted text-[10px] mt-1">{report.total_purchases} transacao(oes)</div>
        </div>
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Total reembolsado</div>
          <div className="text-2xl text-[#E74C3C] font-display">{fmt(report.total_refunded)}</div>
          <div className="text-muted text-[10px] mt-1">{report.total_refunds} estorno(s)</div>
        </div>
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Receita liquida</div>
          <div className={`text-2xl font-display ${report.net_revenue >= 0 ? 'text-[#2ECC71]' : 'text-[#E74C3C]'}`}>{fmt(report.net_revenue)}</div>
        </div>
        <div className="glass-card p-5">
          <div className="text-muted text-xs mb-1">Taxa de churn</div>
          <div className={`text-2xl font-display ${report.refund_rate > 10 ? 'text-[#E74C3C]' : report.refund_rate > 5 ? 'text-[#F39C12]' : 'text-[#2ECC71]'}`}>{report.refund_rate}%</div>
          <div className="text-muted text-[10px] mt-1">{report.total_refunds} de {report.total_purchases} compras</div>
        </div>
      </div>

      {/* Daily breakdown */}
      {report.daily_breakdown.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-stardust text-sm font-medium mb-4">Receita diaria</h3>
          <div className="max-h-64 overflow-y-auto">
            <table className="w-full">
              <thead className="sticky top-0 bg-surface">
                <tr className="border-b border-gold/10">
                  <th className="text-left text-xs text-muted font-normal px-4 py-2">Data</th>
                  <th className="text-right text-xs text-muted font-normal px-4 py-2">Receita</th>
                  <th className="text-right text-xs text-muted font-normal px-4 py-2">Transacoes</th>
                </tr>
              </thead>
              <tbody>
                {report.daily_breakdown.map(d => (
                  <tr key={d.day} className="border-b border-white/[0.03]">
                    <td className="px-4 py-2 text-stardust text-sm">{new Date(d.day + 'T12:00:00').toLocaleDateString('pt-BR')}</td>
                    <td className="px-4 py-2 text-gold text-sm text-right">{fmt(d.revenue)}</td>
                    <td className="px-4 py-2 text-muted text-sm text-right">{d.transactions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Monthly breakdown */}
      {report.monthly_breakdown.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-stardust text-sm font-medium mb-4">Receita mensal</h3>
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
        </div>
      )}

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
          <p className="text-muted text-sm">Nenhuma venda no periodo selecionado</p>
        )}
      </div>
    </div>
  )
}
