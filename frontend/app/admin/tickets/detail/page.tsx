'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

function getAdminHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
}

interface Message { id: string; sender_type: string; sender_name: string; message: string; created_at: string }

export default function AdminTicketDetail() {
  return (
    <Suspense fallback={<div className="text-muted">Carregando...</div>}>
      <AdminTicketDetailContent />
    </Suspense>
  )
}

function AdminTicketDetailContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const ticketId = searchParams.get('id') || ''
  const [ticket, setTicket] = useState<Record<string, unknown> | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [reply, setReply] = useState('')

  useEffect(() => {
    if (!ticketId) return
    fetch(`${API_URL}/admin/api/tickets/${ticketId}`, { headers: getAdminHeaders() })
      .then(r => r.json())
      .then(data => { setTicket(data.ticket); setMessages(data.messages) })
      .catch(() => toast.error('Erro'))
  }, [ticketId])

  async function handleReply(e: React.FormEvent) {
    e.preventDefault()
    const res = await fetch(`${API_URL}/admin/api/tickets/${ticketId}/reply`, {
      method: 'POST', headers: getAdminHeaders(), body: JSON.stringify({ message: reply }),
    })
    if (res.ok) {
      toast.success('Resposta enviada + email enviado ao usuario')
      setReply('')
      const data = await (await fetch(`${API_URL}/admin/api/tickets/${ticketId}`, { headers: getAdminHeaders() })).json()
      setMessages(data.messages)
    } else { toast.error('Erro') }
  }

  async function handleStatusChange(status: string) {
    await fetch(`${API_URL}/admin/api/tickets/${ticketId}/status`, {
      method: 'PATCH', headers: getAdminHeaders(), body: JSON.stringify({ status }),
    })
    toast.success(`Ticket ${status}`)
    setTicket(prev => prev ? { ...prev, status } : prev)
  }

  if (!ticketId) return <div className="text-muted">ID do ticket nao informado.</div>
  if (!ticket) return <div className="text-muted">Carregando...</div>

  return (
    <div className="space-y-6">
      <button onClick={() => router.back()} className="text-muted hover:text-stardust text-sm">&larr; Voltar</button>

      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-2xl text-stardust">{ticket.subject as string}</h2>
          <p className="text-muted text-xs mt-1">{ticket.user_name as string} ({ticket.user_email as string})</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => handleStatusChange('open')} className="px-3 py-1 text-xs rounded-full bg-[#2ECC71]/20 text-[#2ECC71]">Abrir</button>
          <button onClick={() => handleStatusChange('closed')} className="px-3 py-1 text-xs rounded-full bg-muted/20 text-muted">Fechar</button>
        </div>
      </div>

      <div className="space-y-4">
        {messages.map(m => (
          <div key={m.id} className={`glass-card p-4 ${m.sender_type === 'admin' ? 'border-gold/20 ml-12' : 'mr-12'}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-xs font-medium ${m.sender_type === 'admin' ? 'text-gold' : 'text-violet'}`}>{m.sender_name}</span>
              <span className="text-muted text-[10px]">{new Date(m.created_at).toLocaleString('pt-BR')}</span>
            </div>
            <p className="text-stardust/80 text-sm whitespace-pre-wrap">{m.message}</p>
          </div>
        ))}
      </div>

      <form onSubmit={handleReply} className="flex gap-3">
        <textarea value={reply} onChange={e => setReply(e.target.value)}
          placeholder="Responder ao usuario (sera enviado por email tambem)..."
          className="input-field flex-1" rows={3} required />
        <button type="submit" className="btn-primary text-sm self-end">Enviar resposta</button>
      </form>
    </div>
  )
}
