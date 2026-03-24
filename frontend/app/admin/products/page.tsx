'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getProducts, createProduct, toggleProduct, deleteProduct, AdminProduct } from '@/lib/admin-api'

export default function AdminProductsPage() {
  const [products, setProducts] = useState<AdminProduct[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', type: 'credits', price_cents: 2990, credits: 1, create_in_stripe: true })
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const load = () => getProducts().then(setProducts).catch(() => toast.error('Erro ao carregar'))

  useEffect(() => { load() }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    try {
      await createProduct(form)
      toast.success('Produto criado')
      setShowCreate(false)
      setForm({ name: '', description: '', type: 'credits', price_cents: 2990, credits: 1, create_in_stripe: true })
      load()
    } catch (err: unknown) { toast.error(err instanceof Error ? err.message : 'Erro') }
  }

  async function handleToggle(id: string) {
    try {
      const res = await toggleProduct(id)
      toast.success(res.active ? 'Ativado' : 'Desativado')
      load()
    } catch { toast.error('Erro') }
  }

  async function handleDelete(id: string) {
    try { await deleteProduct(id); toast.success('Arquivado'); setConfirmDelete(null); load() }
    catch { toast.error('Erro') }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-2xl text-stardust">Produtos</h2>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary text-sm">
          {showCreate ? 'Cancelar' : '+ Novo Produto'}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="glass-card p-6 space-y-4 max-w-lg">
          <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Nome" className="input-field w-full" required />
          <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Descricao" className="input-field w-full" rows={2} />
          <div className="flex gap-3">
            {['credits', 'one_time', 'subscription'].map(t => (
              <button key={t} type="button" onClick={() => setForm({ ...form, type: t })}
                className={`px-3 py-1 text-xs rounded-full ${form.type === t ? 'bg-gold text-cosmos' : 'text-muted border border-gold/20'}`}>
                {t}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-muted text-xs mb-1 block">Preco (centavos)</label>
              <input type="number" value={form.price_cents} onChange={e => setForm({ ...form, price_cents: Number(e.target.value) })} className="input-field w-full" />
            </div>
            <div>
              <label className="text-muted text-xs mb-1 block">Creditos incluidos</label>
              <input type="number" value={form.credits} onChange={e => setForm({ ...form, credits: Number(e.target.value) })} className="input-field w-full" />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" checked={form.create_in_stripe} onChange={e => setForm({ ...form, create_in_stripe: e.target.checked })} />
            Criar no Stripe automaticamente
          </label>
          <button type="submit" className="btn-primary text-sm w-full">Criar Produto</button>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map(p => (
          <div key={p.id} className={`glass-card p-5 ${!p.active ? 'opacity-50' : ''}`}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-stardust font-medium">{p.name}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full ${p.type === 'credits' ? 'bg-violet/20 text-violet' : 'bg-gold/10 text-gold'}`}>{p.type}</span>
              </div>
              <button onClick={() => handleToggle(p.id)}
                className={`w-10 h-5 rounded-full transition-colors ${p.active ? 'bg-[#2ECC71]' : 'bg-muted/30'}`}>
                <div className={`w-4 h-4 rounded-full bg-white transition-transform ${p.active ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </button>
            </div>
            <p className="text-muted text-xs mb-3">{p.description}</p>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-gold text-lg font-display">R$ {(p.price_cents / 100).toFixed(2)}</span>
                {p.credits > 0 && <span className="text-muted text-xs ml-2">{p.credits} creditos</span>}
              </div>
              {confirmDelete === p.id ? (
                <button onClick={() => handleDelete(p.id)} className="text-[#E74C3C] text-xs font-bold">Confirmar?</button>
              ) : (
                <button onClick={() => setConfirmDelete(p.id)} className="text-muted hover:text-[#E74C3C] text-xs">Arquivar</button>
              )}
            </div>
            {p.stripe_product_id && (
              <div className="mt-2 text-muted text-[10px] font-mono truncate cursor-pointer" onClick={() => { navigator.clipboard.writeText(p.stripe_product_id!); toast.success('Copiado') }}>
                {p.stripe_product_id}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
