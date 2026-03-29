'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { toast } from 'sonner'
import { isAdminLoggedIn } from '@/lib/admin-api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

function getAdminHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
}

interface Ticket { id: string; subject: string; status: string; priority: string; user_name: string; user_email: string; message_count: number; created_at: string }

export default function AdminTicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    fetch(`${API_URL}/admin/api/tickets?page=${page}&status=${statusFilter}`, { headers: getAdminHeaders() })
      .then(r => r.json())
      .then(data => { setTickets(data.tickets); setTotal(data.total) })
      .catch(() => toast.error('Erro ao carregar'))
  }, [page, statusFilter])

  const statusColors: Record<string, string> = {
    open: 'bg-[#2ECC71]/20 text-[#2ECC71]',
    closed: 'bg-muted/20 text-muted',
    waiting: 'bg-[#F39C12]/20 text-[#F39C12]',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-2xl text-stardust">Tickets de Suporte ({total})</h2>
        <div className="flex gap-2">
          {['', 'open', 'closed'].map(s => (
            <button key={s} onClick={() => { setStatusFilter(s); setPage(1) }}
              className={`px-3 py-1 text-xs rounded-full ${statusFilter === s ? 'bg-gold text-cosmos' : 'text-muted border border-gold/20'}`}>
              {s || 'Todos'}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gold/10">
              {['Assunto', 'Usuario', 'Status', 'Mensagens', 'Data', 'Acoes'].map(h => (
                <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tickets.map(t => (
              <tr key={t.id} className="border-b border-white/[0.03] hover:bg-surface-2/50">
                <td className="px-4 py-3 text-stardust text-sm">{t.subject}</td>
                <td className="px-4 py-3 text-muted text-xs">{t.user_name}<br/><span className="text-[10px]">{t.user_email}</span></td>
                <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[t.status] || ''}`}>{t.status}</span></td>
                <td className="px-4 py-3 text-stardust text-sm">{t.message_count}</td>
                <td className="px-4 py-3 text-muted text-xs">{new Date(t.created_at).toLocaleDateString('pt-BR')}</td>
                <td className="px-4 py-3">
                  <Link href={`/admin/tickets/detail?id=${t.id}`} className="text-gold text-xs hover:underline">Abrir</Link>
                </td>
              </tr>
            ))}
            {tickets.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted">Nenhum ticket</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
