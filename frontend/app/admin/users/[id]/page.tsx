'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { getUser, updateUser, manageCredits, deleteUser, banUser } from '@/lib/admin-api'

export default function AdminUserDetail() {
  const params = useParams()
  const router = useRouter()
  const userId = params.id as string
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [editName, setEditName] = useState('')
  const [editPlan, setEditPlan] = useState('')
  const [creditType, setCreditType] = useState('add')
  const [creditAmount, setCreditAmount] = useState(0)
  const [creditReason, setCreditReason] = useState('')
  const [showCreditModal, setShowCreditModal] = useState(false)
  const [tab, setTab] = useState('dados')

  useEffect(() => {
    getUser(userId).then((res) => {
      setData(res)
      const user = res.user as Record<string, string>
      setEditName(user.name)
      setEditPlan(user.plan)
    }).catch(() => toast.error('Erro ao carregar usuario'))
  }, [userId])

  if (!data) return <div className="text-muted">Carregando...</div>

  const user = data.user as Record<string, string>
  const credits = data.credits as Record<string, number>
  const charts = data.charts as Record<string, unknown>[]
  const purchases = data.purchases as Record<string, unknown>[]
  const creditTx = data.credit_transactions as Record<string, unknown>[]

  async function handleSave() {
    try {
      await updateUser(userId, { name: editName, plan: editPlan })
      toast.success('Usuario atualizado')
    } catch { toast.error('Erro ao salvar') }
  }

  async function handleCredits() {
    try {
      await manageCredits(userId, creditType, creditAmount, creditReason)
      toast.success('Creditos atualizados')
      setShowCreditModal(false)
      const res = await getUser(userId)
      setData(res)
    } catch { toast.error('Erro ao gerenciar creditos') }
  }

  const TABS = ['dados', 'creditos', 'mapas', 'atividade', 'compras']

  return (
    <div className="space-y-6">
      <button onClick={() => router.back()} className="text-muted hover:text-stardust text-sm">&larr; Voltar</button>

      <div className="flex items-center gap-4">
        <h2 className="font-display text-2xl text-stardust">{user.name}</h2>
        <span className="text-xs bg-gold/10 text-gold px-2 py-0.5 rounded-full">{user.plan}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full ${user.status === 'active' ? 'bg-[#2ECC71]/20 text-[#2ECC71]' : 'bg-[#E74C3C]/20 text-[#E74C3C]'}`}>{user.status}</span>
      </div>

      <div className="flex gap-2 border-b border-gold/10">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm capitalize ${tab === t ? 'text-gold border-b-2 border-gold' : 'text-muted'}`}
          >{t}</button>
        ))}
      </div>

      {tab === 'dados' && (
        <div className="glass-card p-6 space-y-4 max-w-lg">
          <div>
            <label className="text-muted text-xs mb-1 block">Nome</label>
            <input value={editName} onChange={e => setEditName(e.target.value)} className="input-field w-full" />
          </div>
          <div>
            <label className="text-muted text-xs mb-1 block">Email</label>
            <input value={user.email} disabled className="input-field w-full opacity-50" />
          </div>
          <div>
            <label className="text-muted text-xs mb-1 block">Plano</label>
            <select value={editPlan} onChange={e => setEditPlan(e.target.value)} className="input-field w-full">
              <option value="free">Free</option>
              <option value="pro">Pro</option>
              <option value="superadmin">Super Admin</option>
            </select>
          </div>
          <div className="flex flex-wrap gap-3 pt-2">
            <button onClick={handleSave} className="btn-primary text-sm">Salvar</button>
            <button onClick={async () => {
              const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'
              const token = localStorage.getItem('admin_token')
              const res = await fetch(`${API_URL}/admin/api/users/${userId}/force-reset-password`, {
                method: 'POST', headers: { Authorization: `Bearer ${token}` },
              })
              if (res.ok) toast.success('Usuario devera redefinir a senha no proximo login')
              else toast.error('Erro ao forcar reset')
            }} className="px-4 py-2 text-sm rounded-full border border-[#F39C12]/30 text-[#F39C12] hover:bg-[#F39C12]/10">Resetar senha</button>
            <button onClick={() => { banUser(userId, 'Admin action'); toast.success('Banido') }} className="px-4 py-2 text-sm rounded-full border border-[#E74C3C]/30 text-[#E74C3C] hover:bg-[#E74C3C]/10">Banir</button>
            <button onClick={async () => { await deleteUser(userId); toast.success('Excluido'); router.push('/admin/users') }} className="px-4 py-2 text-sm rounded-full border border-[#E74C3C]/30 text-[#E74C3C] hover:bg-[#E74C3C]/10">Excluir</button>
          </div>
        </div>
      )}

      {tab === 'creditos' && (
        <div className="space-y-4">
          <div className="glass-card p-6 flex gap-8">
            <div><span className="text-muted text-xs">Saldo</span><div className="text-2xl text-gold font-display">{credits.credits_balance}</div></div>
            <div><span className="text-muted text-xs">Comprados</span><div className="text-xl text-stardust">{credits.total_purchased}</div></div>
            <div><span className="text-muted text-xs">Usados</span><div className="text-xl text-stardust">{credits.total_used}</div></div>
            <button onClick={() => setShowCreditModal(true)} className="btn-primary text-sm ml-auto self-center">Gerenciar</button>
          </div>

          {showCreditModal && (
            <div className="glass-card p-6 max-w-md space-y-4">
              <h3 className="text-stardust font-medium">Gerenciar Creditos</h3>
              <div className="flex gap-3">
                <button onClick={() => setCreditType('add')} className={`px-3 py-1 text-sm rounded ${creditType === 'add' ? 'bg-gold text-cosmos' : 'text-muted border border-gold/20'}`}>Adicionar</button>
                <button onClick={() => setCreditType('remove')} className={`px-3 py-1 text-sm rounded ${creditType === 'remove' ? 'bg-[#E74C3C] text-white' : 'text-muted border border-gold/20'}`}>Remover</button>
              </div>
              <input type="number" value={creditAmount} onChange={e => setCreditAmount(Number(e.target.value))} placeholder="Quantidade" className="input-field w-full" />
              <input value={creditReason} onChange={e => setCreditReason(e.target.value)} placeholder="Motivo" className="input-field w-full" />
              <div className="flex gap-3">
                <button onClick={() => setShowCreditModal(false)} className="btn-secondary text-sm">Cancelar</button>
                <button onClick={handleCredits} className="btn-primary text-sm">Confirmar</button>
              </div>
            </div>
          )}

          <div className="glass-card overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gold/10">
                  {['Data', 'Tipo', 'Quantidade', 'Descricao'].map(h => (
                    <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {creditTx.map((tx, i) => (
                  <tr key={i} className="border-b border-white/[0.03]">
                    <td className="px-4 py-2 text-muted text-xs">{new Date(tx.created_at as string).toLocaleString('pt-BR')}</td>
                    <td className="px-4 py-2 text-xs"><span className={`px-2 py-0.5 rounded-full ${(tx.amount as number) > 0 ? 'bg-[#2ECC71]/20 text-[#2ECC71]' : 'bg-[#E74C3C]/20 text-[#E74C3C]'}`}>{tx.type as string}</span></td>
                    <td className="px-4 py-2 text-stardust text-sm">{(tx.amount as number) > 0 ? '+' : ''}{tx.amount as number}</td>
                    <td className="px-4 py-2 text-muted text-xs">{tx.description as string}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'mapas' && (
        <div className="glass-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gold/10">
                {['Nome', 'Nascimento', 'Cidade', 'Gerado em'].map(h => (
                  <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {charts.map((c, i) => (
                <tr key={i} className="border-b border-white/[0.03]">
                  <td className="px-4 py-2 text-stardust text-sm">{c.name as string}</td>
                  <td className="px-4 py-2 text-muted text-xs">{c.birth_date as string}</td>
                  <td className="px-4 py-2 text-muted text-xs">{c.birth_city as string}</td>
                  <td className="px-4 py-2 text-muted text-xs">{new Date(c.created_at as string).toLocaleString('pt-BR')}</td>
                </tr>
              ))}
              {charts.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-6 text-center text-muted text-sm">Nenhum mapa</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'atividade' && (
        <div className="glass-card overflow-hidden">
          <div className="px-4 py-3 border-b border-gold/10">
            <h3 className="text-stardust text-sm">Mapas gerados ({((data.generations || []) as Record<string, unknown>[]).length})</h3>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-gold/10">
                {['Data', 'Nome', 'Nascimento', 'Cidade'].map(h => (
                  <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {((data.generations || []) as Record<string, unknown>[]).map((g, i) => (
                <tr key={i} className="border-b border-white/[0.03]">
                  <td className="px-4 py-2 text-muted text-xs">{new Date(g.created_at as string).toLocaleString('pt-BR')}</td>
                  <td className="px-4 py-2 text-stardust text-sm">{g.name as string}</td>
                  <td className="px-4 py-2 text-muted text-xs">{g.birth_date as string}</td>
                  <td className="px-4 py-2 text-muted text-xs">{g.birth_city as string}</td>
                </tr>
              ))}
              {((data.generations || []) as Record<string, unknown>[]).length === 0 && (
                <tr><td colSpan={4} className="px-4 py-6 text-center text-muted text-sm">Nenhuma geracao registrada</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'compras' && (
        <div className="glass-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gold/10">
                {['Data', 'Produto', 'Valor', 'Status', 'Stripe ID'].map(h => (
                  <th key={h} className="text-left text-xs text-muted font-normal px-4 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {purchases.map((p, i) => (
                <tr key={i} className="border-b border-white/[0.03]">
                  <td className="px-4 py-2 text-muted text-xs">{new Date(p.created_at as string).toLocaleString('pt-BR')}</td>
                  <td className="px-4 py-2 text-stardust text-xs">{(p.product_name as string) || (p.product_type as string)}</td>
                  <td className="px-4 py-2 text-stardust text-sm">R$ {((p.amount_cents as number) / 100).toFixed(2)}</td>
                  <td className="px-4 py-2"><span className={`text-xs px-2 py-0.5 rounded-full ${p.status === 'completed' ? 'bg-[#2ECC71]/20 text-[#2ECC71]' : p.status === 'refunded' ? 'bg-[#E74C3C]/20 text-[#E74C3C]' : 'bg-[#F39C12]/20 text-[#F39C12]'}`}>{p.status as string}</span></td>
                  <td className="px-4 py-2 text-muted text-xs font-mono">{(p.stripe_payment_id as string)?.slice(0, 20)}</td>
                </tr>
              ))}
              {purchases.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-muted text-sm">Nenhuma compra</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
