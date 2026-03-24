'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { toast } from 'sonner'
import { getUsers, deleteUser, banUser, AdminUser } from '@/lib/admin-api'

const STATUS_BADGE: Record<string, string> = {
  active: 'bg-[#2ECC71]/20 text-[#2ECC71]',
  banned: 'bg-[#E74C3C]/20 text-[#E74C3C]',
  suspended: 'bg-[#F39C12]/20 text-[#F39C12]',
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [search, setSearch] = useState('')
  const [searchDebounced, setSearchDebounced] = useState('')
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  useEffect(() => {
    const t = setTimeout(() => setSearchDebounced(search), 300)
    return () => clearTimeout(t)
  }, [search])

  const load = useCallback(() => {
    getUsers(page, 20, searchDebounced).then(res => {
      setUsers(res.users)
      setTotal(res.total)
      setPages(res.pages)
    }).catch(() => toast.error('Erro ao carregar usuarios'))
  }, [page, searchDebounced])

  useEffect(() => { load() }, [load])

  async function handleDelete(id: string) {
    try {
      await deleteUser(id)
      toast.success('Usuario excluido')
      setConfirmDelete(null)
      load()
    } catch { toast.error('Erro ao excluir') }
  }

  async function handleBan(id: string) {
    try {
      await banUser(id, 'Banido pelo admin')
      toast.success('Usuario banido')
      load()
    } catch { toast.error('Erro ao banir') }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-2xl text-stardust">Usuarios ({total})</h2>
        <input
          type="text"
          placeholder="Buscar por nome ou email..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          className="input-field w-72 text-sm"
        />
      </div>

      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gold/10">
              {['Nome', 'Email', 'Plano', 'Creditos', 'Mapas', 'Status', 'Acoes'].map(h => (
                <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-b border-white/[0.03] hover:bg-surface-2/50">
                <td className="px-4 py-3 text-stardust text-sm">{u.name}</td>
                <td className="px-4 py-3 text-muted text-sm">{u.email}</td>
                <td className="px-4 py-3"><span className="text-xs bg-gold/10 text-gold px-2 py-0.5 rounded-full">{u.plan}</span></td>
                <td className="px-4 py-3 text-stardust text-sm">{u.credits}</td>
                <td className="px-4 py-3 text-stardust text-sm">{u.chart_count}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_BADGE[u.status] || 'bg-muted/20 text-muted'}`}>
                    {u.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <Link href={`/admin/users/${u.id}`} className="text-gold hover:text-gold/80 text-xs">Ver</Link>
                    {u.status !== 'banned' && (
                      <button onClick={() => handleBan(u.id)} className="text-[#F39C12] hover:text-[#F39C12]/80 text-xs">Banir</button>
                    )}
                    {confirmDelete === u.id ? (
                      <button onClick={() => handleDelete(u.id)} className="text-[#E74C3C] text-xs font-bold">Confirmar?</button>
                    ) : (
                      <button onClick={() => setConfirmDelete(u.id)} className="text-[#E74C3C] hover:text-[#E74C3C]/80 text-xs">Excluir</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex justify-center gap-2">
          {Array.from({ length: pages }, (_, i) => (
            <button
              key={i}
              onClick={() => setPage(i + 1)}
              className={`px-3 py-1 text-sm rounded ${page === i + 1 ? 'bg-gold text-cosmos' : 'text-muted hover:text-stardust'}`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
