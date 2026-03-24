'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getTransactions, getRevenue } from '@/lib/admin-api'

export default function AdminTransactionsPage() {
  const [transactions, setTransactions] = useState<Record<string, unknown>[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [revenue, setRevenue] = useState<{ monthly: number; yearly: number; total_transactions: number } | null>(null)

  useEffect(() => {
    getTransactions(page).then(res => {
      setTransactions(res.transactions)
      setTotal(res.total)
      setPages(res.pages)
    }).catch(() => toast.error('Erro ao carregar'))
    getRevenue().then(setRevenue).catch(() => {})
  }, [page])

  return (
    <div className="space-y-6">
      <h2 className="font-display text-2xl text-stardust">Transacoes ({total})</h2>

      {revenue && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="glass-card p-5">
            <div className="text-muted text-xs mb-1">Receita do mes</div>
            <div className="text-2xl text-gold font-display">R$ {(revenue.monthly / 100).toFixed(2)}</div>
          </div>
          <div className="glass-card p-5">
            <div className="text-muted text-xs mb-1">Receita do ano</div>
            <div className="text-2xl text-stardust font-display">R$ {(revenue.yearly / 100).toFixed(2)}</div>
          </div>
          <div className="glass-card p-5">
            <div className="text-muted text-xs mb-1">Total transacoes</div>
            <div className="text-2xl text-stardust font-display">{revenue.total_transactions}</div>
          </div>
        </div>
      )}

      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gold/10">
              {['Data', 'Usuario', 'Tipo', 'Valor', 'Status', 'Stripe ID'].map(h => (
                <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {transactions.map((t, i) => (
              <tr key={i} className="border-b border-white/[0.03]">
                <td className="px-4 py-3 text-muted text-xs">{new Date(t.created_at as string).toLocaleString('pt-BR')}</td>
                <td className="px-4 py-3 text-stardust text-sm">{(t.user_name as string) || '-'}</td>
                <td className="px-4 py-3 text-muted text-xs">{t.product_type as string}</td>
                <td className="px-4 py-3 text-stardust text-sm">R$ {((t.amount_cents as number) / 100).toFixed(2)}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    t.status === 'completed' ? 'bg-[#2ECC71]/20 text-[#2ECC71]' :
                    t.status === 'pending' ? 'bg-[#F39C12]/20 text-[#F39C12]' :
                    'bg-[#E74C3C]/20 text-[#E74C3C]'
                  }`}>{t.status as string}</span>
                </td>
                <td className="px-4 py-3 text-muted text-[10px] font-mono cursor-pointer"
                    onClick={() => { navigator.clipboard.writeText(t.stripe_payment_id as string); toast.success('Copiado') }}>
                  {(t.stripe_payment_id as string)?.slice(0, 25)}...
                </td>
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted">Nenhuma transacao</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="flex justify-center gap-2">
          {Array.from({ length: pages }, (_, i) => (
            <button key={i} onClick={() => setPage(i + 1)}
              className={`px-3 py-1 text-sm rounded ${page === i + 1 ? 'bg-gold text-cosmos' : 'text-muted'}`}>
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
