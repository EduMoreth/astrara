'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getLogs } from '@/lib/admin-api'

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<Record<string, unknown>[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)

  useEffect(() => {
    getLogs(page).then(res => {
      setLogs(res.logs)
      setTotal(res.total)
      setPages(res.pages)
    }).catch(() => toast.error('Erro ao carregar'))
  }, [page])

  return (
    <div className="space-y-6">
      <h2 className="font-display text-2xl text-stardust">Logs de Atividade ({total})</h2>

      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gold/10">
              {['Data/Hora', 'Admin', 'Acao', 'Tipo', 'Alvo', 'Detalhes'].map(h => (
                <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map((l, i) => (
              <tr key={i} className="border-b border-white/[0.03]">
                <td className="px-4 py-3 text-muted text-xs">{new Date(l.created_at as string).toLocaleString('pt-BR')}</td>
                <td className="px-4 py-3 text-stardust text-xs">{(l.admin_email as string)?.split('@')[0]}</td>
                <td className="px-4 py-3"><span className="text-xs bg-gold/10 text-gold px-2 py-0.5 rounded-full">{l.action as string}</span></td>
                <td className="px-4 py-3 text-muted text-xs">{l.target_type as string || '-'}</td>
                <td className="px-4 py-3 text-muted text-[10px] font-mono">{(l.target_id as string)?.slice(0, 12) || '-'}</td>
                <td className="px-4 py-3 text-muted text-[10px] font-mono max-w-[200px] truncate">
                  {l.details ? JSON.stringify(l.details).slice(0, 50) : '-'}
                </td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted">Nenhum log</td></tr>
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
