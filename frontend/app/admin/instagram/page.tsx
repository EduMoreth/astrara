'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

function getAdminHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
}

interface Post {
  id: string
  post_date: string
  horoscope_text: string
  transits_text: string
  instagram_permalink: string
  status: string
  error_message: string | null
  published_at: string | null
}

export default function AdminInstagramPage() {
  const [posts, setPosts] = useState<Post[]>([])
  const [total, setTotal] = useState(0)
  const [triggering, setTriggering] = useState(false)
  const [triggerDate, setTriggerDate] = useState(new Date().toISOString().slice(0, 10))

  useEffect(() => {
    fetch(`${API_URL}/admin/api/instagram/posts`, { headers: getAdminHeaders() })
      .then(r => r.json())
      .then(data => { setPosts(data.posts); setTotal(data.total) })
      .catch(() => toast.error('Erro ao carregar posts'))
  }, [])

  async function handleTrigger() {
    setTriggering(true)
    toast.info('Gerando conteudo com IA + imagem... isso pode levar ate 2 minutos.')
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 120000) // 2 min timeout

      const res = await fetch(`${API_URL}/admin/api/instagram/posts/trigger`, {
        method: 'POST',
        headers: getAdminHeaders(),
        body: JSON.stringify({ date: triggerDate }),
        signal: controller.signal,
      })
      clearTimeout(timeout)

      const data = await res.json()
      if (data.success) {
        if (data.status === 'published') {
          toast.success('Post publicado no Instagram com sucesso!')
        } else if (data.status === 'already_published') {
          toast.info('Post de hoje ja foi publicado.')
        } else {
          toast.error(`Status: ${data.status} - ${data.error || ''}`)
        }
        // Reload
        const reload = await fetch(`${API_URL}/admin/api/instagram/posts`, { headers: getAdminHeaders() })
        const reloadData = await reload.json()
        setPosts(reloadData.posts)
        setTotal(reloadData.total)
      } else {
        toast.error(data.error || 'Erro ao publicar')
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao disparar post')
    } finally {
      setTriggering(false)
    }
  }

  const statusColors: Record<string, string> = {
    published: 'bg-[#2ECC71]/20 text-[#2ECC71]',
    failed: 'bg-[#E74C3C]/20 text-[#E74C3C]',
    pending: 'bg-[#F39C12]/20 text-[#F39C12]',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-2xl text-stardust">Posts do Instagram ({total})</h2>
      </div>

      {/* Trigger card */}
      <div className="glass-card p-6">
        <h3 className="text-gold text-sm font-medium uppercase tracking-wider mb-4">Publicar Manualmente</h3>
        <div className="flex items-end gap-4">
          <div>
            <label className="text-muted text-xs block mb-1">Data do post</label>
            <input
              type="date"
              value={triggerDate}
              onChange={e => setTriggerDate(e.target.value)}
              className="input-field text-sm py-2 px-3"
            />
          </div>
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="btn-primary text-sm"
          >
            {triggering ? 'Gerando e publicando...' : 'Publicar agora'}
          </button>
        </div>
        <p className="text-muted text-xs mt-3">
          O scheduler automatico publica diariamente as 7h (Brasilia). Use este botao para testes ou republicacao.
        </p>
      </div>

      {/* Posts table */}
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gold/10">
              {['Data', 'Horoscopo', 'Status', 'Publicado', 'Link', 'Acoes'].map(h => (
                <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {posts.map(p => (
              <tr key={p.id} className="border-b border-white/[0.03]">
                <td className="px-4 py-3 text-stardust text-sm">{p.post_date}</td>
                <td className="px-4 py-3 text-muted text-xs max-w-[200px] truncate">{p.horoscope_text?.slice(0, 80)}...</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[p.status] || ''}`}>{p.status}</span>
                </td>
                <td className="px-4 py-3 text-muted text-xs">
                  {p.published_at ? new Date(p.published_at).toLocaleString('pt-BR') : '-'}
                </td>
                <td className="px-4 py-3">
                  {p.instagram_permalink ? (
                    <a href={p.instagram_permalink} target="_blank" rel="noopener noreferrer" className="text-gold text-xs hover:underline">
                      Ver post
                    </a>
                  ) : '-'}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={async () => {
                      setTriggering(true)
                      try {
                        await fetch(`${API_URL}/admin/api/instagram/posts/trigger`, {
                          method: 'POST', headers: getAdminHeaders(),
                          body: JSON.stringify({ date: p.post_date }),
                        })
                        toast.success('Post republicado!')
                      } catch { toast.error('Erro') }
                      finally { setTriggering(false) }
                    }}
                    className="text-gold text-xs hover:underline"
                  >
                    Republicar
                  </button>
                  {p.error_message && (
                    <span className="text-[#E74C3C] text-[10px] block mt-1" title={p.error_message}>
                      Erro: {p.error_message.slice(0, 40)}...
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {posts.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted">Nenhum post ainda. Clique &quot;Publicar agora&quot; para testar.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
