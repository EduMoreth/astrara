'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

interface Ticket {
  id: string
  subject: string
  status: string
  priority: string
  created_at: string
  message_count: number
}

interface Message {
  id: string
  sender_type: string
  sender_name: string
  message: string
  created_at: string
}

function getHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('astrara_token') : null
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export default function SupportPage() {
  const router = useRouter()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selectedTicket, setSelectedTicket] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [ticketDetail, setTicketDetail] = useState<Ticket | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newSubject, setNewSubject] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [replyText, setReplyText] = useState('')
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('astrara_token')
    if (!token) { router.push('/auth/login'); return }
    setIsLoggedIn(true)
    loadTickets()
  }, [router])

  async function loadTickets() {
    try {
      const res = await fetch(`${API_URL}/support/tickets`, { headers: getHeaders() })
      if (res.status === 401) {
        localStorage.removeItem('astrara_token')
        router.push('/auth/login')
        return
      }
      if (res.ok) {
        const data = await res.json()
        setTickets(Array.isArray(data) ? data : [])
      }
    } catch { /* network error: keep current list */ }
  }

  async function loadTicket(id: string) {
    try {
      const res = await fetch(`${API_URL}/support/tickets/${id}`, { headers: getHeaders() })
      if (res.ok) {
        const data = await res.json()
        if (data && data.ticket) {
          setTicketDetail(data.ticket)
          setMessages(Array.isArray(data.messages) ? data.messages : [])
          setSelectedTicket(id)
        }
      }
    } catch {
      toast.error('Erro ao carregar o ticket')
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    let res: Response
    try {
      res = await fetch(`${API_URL}/support/tickets`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ subject: newSubject, message: newMessage }),
      })
    } catch {
      toast.error('Erro de conexao. Tente novamente.')
      return
    }
    if (res.ok) {
      toast.success('Ticket criado com sucesso')
      setShowCreate(false)
      setNewSubject('')
      setNewMessage('')
      loadTickets()
    } else {
      toast.error('Erro ao criar ticket')
    }
  }

  async function handleReply(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedTicket) return
    try {
      const res = await fetch(`${API_URL}/support/tickets/${selectedTicket}/reply`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ message: replyText }),
      })
      if (res.ok) {
        toast.success('Resposta enviada')
        setReplyText('')
        loadTicket(selectedTicket)
      } else {
        toast.error('Erro ao enviar resposta. Tente novamente.')
      }
    } catch {
      toast.error('Erro de conexao. Tente novamente.')
    }
  }

  if (!isLoggedIn) return null

  const statusColors: Record<string, string> = {
    open: 'bg-[#2ECC71]/20 text-[#2ECC71]',
    closed: 'bg-muted/20 text-muted',
    waiting: 'bg-[#F39C12]/20 text-[#F39C12]',
  }

  return (
    <main className="relative min-h-screen">
      <StarBackground />
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">Astrara</Link>
        <Link href="/chart" className="text-muted hover:text-stardust text-sm">Voltar ao mapa</Link>
      </nav>

      <div className="relative z-10 px-6 py-8 max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display text-3xl text-stardust">Suporte</h1>
          <button onClick={() => setShowCreate(!showCreate)} className="btn-primary text-sm">
            {showCreate ? 'Cancelar' : '+ Novo ticket'}
          </button>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} className="glass-card p-6 space-y-4 mb-8">
            <input value={newSubject} onChange={e => setNewSubject(e.target.value)} placeholder="Assunto" className="input-field w-full" required />
            <textarea value={newMessage} onChange={e => setNewMessage(e.target.value)} placeholder="Descreva seu problema ou duvida..." className="input-field w-full" rows={4} required />
            <button type="submit" className="btn-primary text-sm">Enviar ticket</button>
          </form>
        )}

        {!selectedTicket ? (
          <div className="space-y-3">
            {tickets.map(t => (
              <button key={t.id} onClick={() => loadTicket(t.id)}
                className="glass-card p-5 w-full text-left hover:border-gold/30 transition-colors">
                <div className="flex items-center justify-between">
                  <h3 className="text-stardust font-medium">{t.subject}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[t.status] || statusColors.open}`}>{t.status}</span>
                </div>
                <div className="flex gap-4 mt-2 text-muted text-xs">
                  <span>{new Date(t.created_at).toLocaleDateString('pt-BR')}</span>
                  <span>{t.message_count} mensagen{t.message_count !== 1 ? 's' : ''}</span>
                </div>
              </button>
            ))}
            {tickets.length === 0 && !showCreate && (
              <div className="glass-card p-12 text-center">
                <p className="text-muted mb-4">Nenhum ticket aberto</p>
                <button onClick={() => setShowCreate(true)} className="btn-primary text-sm">Criar primeiro ticket</button>
              </div>
            )}
          </div>
        ) : (
          <div>
            <button onClick={() => { setSelectedTicket(null); setMessages([]) }} className="text-muted hover:text-stardust text-sm mb-4">&larr; Voltar</button>
            {ticketDetail && (
              <div className="mb-6">
                <h2 className="text-stardust text-xl font-display">{ticketDetail.subject}</h2>
                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[ticketDetail.status] || statusColors.open}`}>{ticketDetail.status}</span>
              </div>
            )}
            <div className="space-y-4 mb-6">
              {messages.map(m => (
                <div key={m.id} className={`glass-card p-4 ${m.sender_type === 'admin' ? 'border-gold/20 ml-8' : 'mr-8'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs font-medium ${m.sender_type === 'admin' ? 'text-gold' : 'text-violet'}`}>{m.sender_name}</span>
                    <span className="text-muted text-[10px]">{new Date(m.created_at).toLocaleString('pt-BR')}</span>
                  </div>
                  <p className="text-stardust/80 text-sm whitespace-pre-wrap">{m.message}</p>
                </div>
              ))}
            </div>
            {ticketDetail?.status !== 'closed' && (
              <form onSubmit={handleReply} className="flex gap-3">
                <input value={replyText} onChange={e => setReplyText(e.target.value)} placeholder="Escreva sua resposta..." className="input-field flex-1" required />
                <button type="submit" className="btn-primary text-sm">Enviar</button>
              </form>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
