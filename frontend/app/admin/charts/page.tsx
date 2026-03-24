'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getCharts, deleteChart } from '@/lib/admin-api'

export default function AdminChartsPage() {
  const [charts, setCharts] = useState<Record<string, unknown>[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  useEffect(() => {
    getCharts(page).then(res => {
      setCharts(res.charts)
      setTotal(res.total)
      setPages(res.pages)
    }).catch(() => toast.error('Erro ao carregar'))
  }, [page])

  async function handleDelete(id: string) {
    try { await deleteChart(id); toast.success('Mapa excluido'); setConfirmDelete(null); setPage(1) }
    catch { toast.error('Erro') }
  }

  return (
    <div className="space-y-6">
      <h2 className="font-display text-2xl text-stardust">Mapas ({total})</h2>

      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gold/10">
              {['Usuario', 'Nativo', 'Nascimento', 'Cidade', 'Gerado em', 'Acoes'].map(h => (
                <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {charts.map((c) => (
              <tr key={c.id as string} className="border-b border-white/[0.03]">
                <td className="px-4 py-3 text-stardust text-sm">{(c.user_name as string) || '-'}</td>
                <td className="px-4 py-3 text-stardust text-sm">{c.name as string}</td>
                <td className="px-4 py-3 text-muted text-xs">{c.birth_date as string} {c.birth_time as string}</td>
                <td className="px-4 py-3 text-muted text-xs">{c.birth_city as string}</td>
                <td className="px-4 py-3 text-muted text-xs">{new Date(c.created_at as string).toLocaleString('pt-BR')}</td>
                <td className="px-4 py-3">
                  {confirmDelete === (c.id as string) ? (
                    <button onClick={() => handleDelete(c.id as string)} className="text-[#E74C3C] text-xs font-bold">Confirmar?</button>
                  ) : (
                    <button onClick={() => setConfirmDelete(c.id as string)} className="text-muted hover:text-[#E74C3C] text-xs">Excluir</button>
                  )}
                </td>
              </tr>
            ))}
            {charts.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted">Nenhum mapa</td></tr>
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
