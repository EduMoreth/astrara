'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getProducts, createProduct, toggleProduct, deleteProduct, updateProduct, AdminProduct } from '@/lib/admin-api'

export default function AdminProductsPage() {
  const [products, setProducts] = useState<AdminProduct[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editPrice, setEditPrice] = useState('')
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [editCredits, setEditCredits] = useState(0)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', type: 'credits', price_reais: '29.90', credits: 1, create_in_stripe: true })
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const load = () => getProducts().then(setProducts).catch(() => toast.error('Erro ao carregar'))

  useEffect(() => { load() }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    const price_cents = Math.round(parseFloat(form.price_reais.replace(',', '.')) * 100)
    if (isNaN(price_cents) || price_cents <= 0) {
      toast.error('Preco invalido')
      return
    }
    try {
      await createProduct({ ...form, price_cents, price_reais: undefined })
      toast.success('Produto criado')
      setShowCreate(false)
      setForm({ name: '', description: '', type: 'credits', price_reais: '29.90', credits: 1, create_in_stripe: true })
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

  const typeLabels: Record<string, string> = {
    credits: 'Creditos',
    one_time: 'Avulso',
    subscription: 'Assinatura',
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
          <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Nome do produto" className="input-field w-full" required />
          <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Descricao" className="input-field w-full" rows={2} />
          <div className="flex gap-3">
            {Object.entries(typeLabels).map(([key, label]) => (
              <button key={key} type="button" onClick={() => setForm({ ...form, type: key })}
                className={`px-3 py-1 text-xs rounded-full ${form.type === key ? 'bg-gold text-cosmos' : 'text-muted border border-gold/20'}`}>
                {label}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-muted text-xs mb-1 block">Preco (R$)</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted text-sm">R$</span>
                <input
                  type="text"
                  value={form.price_reais}
                  onChange={e => setForm({ ...form, price_reais: e.target.value })}
                  placeholder="29,90"
                  className="input-field w-full pl-10"
                />
              </div>
            </div>
            <div>
              <label className="text-muted text-xs mb-1 block">Creditos incluidos</label>
              <input type="number" value={form.credits} onChange={e => setForm({ ...form, credits: Number(e.target.value) })} className="input-field w-full" />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" checked={form.create_in_stripe} onChange={e => setForm({ ...form, create_in_stripe: e.target.checked })} className="accent-gold" />
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
                <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${
                  p.type === 'credits' ? 'bg-violet/20 text-violet' :
                  p.type === 'subscription' ? 'bg-gold/10 text-gold' :
                  'bg-surface-2 text-muted'
                }`}>{typeLabels[p.type] || p.type}</span>
              </div>
              <button onClick={() => handleToggle(p.id)}
                className={`w-10 h-5 rounded-full transition-colors ${p.active ? 'bg-[#2ECC71]' : 'bg-muted/30'}`}>
                <div className={`w-4 h-4 rounded-full bg-white transition-transform ${p.active ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </button>
            </div>
            {editingId === p.id ? (
              /* Edit mode */
              <div className="space-y-3 mt-2">
                <input value={editName} onChange={e => setEditName(e.target.value)} className="input-field w-full text-sm" placeholder="Nome" />
                <textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} className="input-field w-full text-sm" rows={2} placeholder="Descricao" />
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-muted text-[10px]">Preco (R$)</label>
                    <input value={editPrice} onChange={e => setEditPrice(e.target.value)} className="input-field w-full text-sm" />
                  </div>
                  <div>
                    <label className="text-muted text-[10px]">Creditos</label>
                    <input type="number" value={editCredits} onChange={e => setEditCredits(Number(e.target.value))} className="input-field w-full text-sm" />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={async () => {
                    const price_cents = Math.round(parseFloat(editPrice.replace(',', '.')) * 100)
                    try {
                      await updateProduct(p.id, { name: editName, description: editDesc, price_cents, credits: editCredits })
                      toast.success('Produto atualizado')
                      setEditingId(null)
                      load()
                    } catch { toast.error('Erro ao salvar') }
                  }} className="btn-primary text-xs py-2 px-4">Salvar</button>
                  <button onClick={() => setEditingId(null)} className="text-muted text-xs hover:text-stardust">Cancelar</button>
                </div>
              </div>
            ) : (
              /* View mode */
              <>
                <p className="text-muted text-xs mb-3">{p.description}</p>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-gold text-lg font-display">R$ {(p.price_cents / 100).toFixed(2).replace('.', ',')}</span>
                    {p.credits > 0 && <span className="text-muted text-xs ml-2">{p.credits} credito{p.credits > 1 ? 's' : ''}</span>}
                  </div>
                  <div className="flex gap-3">
                    <button onClick={() => {
                      setEditingId(p.id)
                      setEditName(p.name)
                      setEditDesc(p.description || '')
                      setEditPrice((p.price_cents / 100).toFixed(2).replace('.', ','))
                      setEditCredits(p.credits)
                    }} className="text-gold text-xs hover:underline">Editar</button>
                    {confirmDelete === p.id ? (
                      <button onClick={() => handleDelete(p.id)} className="text-[#E74C3C] text-xs font-bold">Confirmar?</button>
                    ) : (
                      <button onClick={() => setConfirmDelete(p.id)} className="text-muted hover:text-[#E74C3C] text-xs">Arquivar</button>
                    )}
                  </div>
                </div>
                {p.stripe_product_id && (
                  <div className="mt-2 text-muted text-[10px] font-mono truncate cursor-pointer" onClick={() => { navigator.clipboard.writeText(p.stripe_product_id!); toast.success('Copiado') }}>
                    Stripe: {p.stripe_product_id}
                  </div>
                )}
              </>
            )}
          </div>
        ))}
        {products.length === 0 && !showCreate && (
          <div className="glass-card p-8 text-center col-span-full">
            <p className="text-muted">Nenhum produto cadastrado</p>
            <button onClick={() => setShowCreate(true)} className="btn-primary text-sm mt-4">Criar primeiro produto</button>
          </div>
        )}
      </div>
    </div>
  )
}
