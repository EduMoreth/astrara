'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { toast } from 'sonner'
import StarBackground from '@/components/StarBackground'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

function getHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('astrara_token') : null
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
}

export default function AccountPage() {
  const router = useRouter()
  const [user, setUser] = useState<Record<string, string> | null>(null)
  const [credits, setCredits] = useState({ credits_balance: 0, total_purchased: 0, total_used: 0 })
  const [editName, setEditName] = useState('')
  const [showDelete, setShowDelete] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [showChangePassword, setShowChangePassword] = useState(false)
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('astrara_token')
    if (!token) { router.push('/auth/login'); return }

    fetch(`${API_URL}/user/me`, { headers: getHeaders() })
      .then(r => r.json())
      .then(d => { setUser(d); setEditName(d.name) })
      .catch(() => router.push('/auth/login'))

    fetch(`${API_URL}/user/credits`, { headers: getHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(setCredits)
      .catch((err) => {
        console.error('Credits fetch error:', err)
        // Initialize with zeros if endpoint fails
        setCredits({ credits_balance: 0, total_purchased: 0, total_used: 0 })
      })
  }, [router])

  async function handleUpdateName() {
    const res = await fetch(`${API_URL}/user/me`, {
      method: 'PATCH', headers: getHeaders(), body: JSON.stringify({ name: editName }),
    })
    if (res.ok) toast.success('Nome atualizado')
    else toast.error('Erro ao atualizar')
  }

  async function handleExportData() {
    const token = localStorage.getItem('astrara_token')
    const res = await fetch(`${API_URL}/user/export-data`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.ok) {
      const blob = await res.blob()
      const { downloadFile } = await import('@/lib/download')
      await downloadFile(blob, 'astrara-meus-dados.json')
      toast.success('Dados exportados!')
    } else toast.error('Erro ao exportar')
  }

  async function handleDeleteAccount() {
    if (deleteConfirm !== 'EXCLUIR') { toast.error('Digite EXCLUIR para confirmar'); return }
    const res = await fetch(`${API_URL}/user/delete-account`, {
      method: 'POST', headers: getHeaders(),
      body: JSON.stringify({ password: deletePassword, confirmation: deleteConfirm }),
    })
    if (res.ok) {
      localStorage.removeItem('astrara_token')
      toast.success('Conta excluida. Todos os dados foram removidos.')
      router.push('/')
    } else {
      const err = await res.json()
      toast.error(err.detail || 'Erro ao excluir conta')
    }
  }

  async function handleChangePassword() {
    const res = await fetch(`${API_URL}/user/change-password`, {
      method: 'POST', headers: getHeaders(),
      body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
    })
    if (res.ok) {
      toast.success('Senha alterada com sucesso')
      setShowChangePassword(false); setCurrentPw(''); setNewPw('')
    } else {
      const err = await res.json()
      toast.error(err.detail || 'Erro ao alterar senha')
    }
  }

  if (!user) return null

  return (
    <main className="relative min-h-screen">
      <StarBackground />
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-4xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">Astrara</Link>
        <Link href="/chart" className="text-muted hover:text-stardust text-sm">Voltar ao mapa</Link>
      </nav>

      <div className="relative z-10 px-6 py-8 max-w-2xl mx-auto space-y-6">
        <h1 className="font-display text-3xl text-stardust">Minha Conta</h1>

        {/* Profile */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-gold text-sm font-medium uppercase tracking-wider">Dados Pessoais</h2>
          <div>
            <label className="text-muted text-xs block mb-1">Nome</label>
            <div className="flex gap-2">
              <input value={editName} onChange={e => setEditName(e.target.value)} className="input-field flex-1" />
              <button onClick={handleUpdateName} className="btn-primary text-xs px-4">Salvar</button>
            </div>
          </div>
          <div>
            <label className="text-muted text-xs block mb-1">Email</label>
            <input value={user.email} disabled className="input-field w-full opacity-50" />
          </div>
          <div>
            <label className="text-muted text-xs block mb-1">Plano</label>
            <span className="text-xs bg-gold/10 text-gold px-3 py-1 rounded-full">{user.plan}</span>
          </div>
        </div>

        {/* Credits */}
        <div className="glass-card p-6">
          <h2 className="text-gold text-sm font-medium uppercase tracking-wider mb-4">Creditos</h2>
          <div className="flex gap-6">
            <div><span className="text-muted text-xs block">Saldo</span><span className="text-2xl text-gold font-display">{credits.credits_balance}</span></div>
            <div><span className="text-muted text-xs block">Comprados</span><span className="text-lg text-stardust">{credits.total_purchased}</span></div>
            <div><span className="text-muted text-xs block">Usados</span><span className="text-lg text-stardust">{credits.total_used}</span></div>
          </div>
        </div>

        {/* Security */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-gold text-sm font-medium uppercase tracking-wider">Seguranca</h2>
          {!showChangePassword ? (
            <button onClick={() => setShowChangePassword(true)} className="btn-secondary text-xs">Alterar senha</button>
          ) : (
            <div className="space-y-3 max-w-sm">
              <input type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} placeholder="Senha atual" className="input-field w-full" />
              <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="Nova senha (min. 6 caracteres)" className="input-field w-full" />
              <div className="flex gap-2">
                <button onClick={handleChangePassword} className="btn-primary text-xs">Salvar nova senha</button>
                <button onClick={() => setShowChangePassword(false)} className="text-muted text-xs">Cancelar</button>
              </div>
            </div>
          )}
        </div>

        {/* LGPD Rights */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-gold text-sm font-medium uppercase tracking-wider">Seus Direitos (LGPD)</h2>
          <p className="text-muted text-xs leading-relaxed">
            Conforme a Lei Geral de Protecao de Dados (Lei 13.709/2018), voce tem direito a acessar, corrigir, exportar e solicitar a exclusao dos seus dados pessoais.
          </p>

          <div className="flex flex-wrap gap-3">
            <button onClick={handleExportData} className="btn-secondary text-xs">
              Exportar meus dados (JSON)
            </button>
            <Link href="/support" className="btn-secondary text-xs">
              Solicitar correcao de dados
            </Link>
          </div>
        </div>

        {/* Danger zone */}
        <div className="glass-card p-6 border-[#E74C3C]/20 space-y-4">
          <h2 className="text-[#E74C3C] text-sm font-medium uppercase tracking-wider">Zona de Perigo</h2>
          {!showDelete ? (
            <button onClick={() => setShowDelete(true)} className="px-4 py-2 text-xs text-[#E74C3C] border border-[#E74C3C]/30 rounded-full hover:bg-[#E74C3C]/10">
              Excluir minha conta
            </button>
          ) : (
            <div className="space-y-3 max-w-sm">
              <p className="text-[#E74C3C] text-xs">
                Esta acao e irreversivel. Todos os seus dados, mapas, creditos e historico serao permanentemente excluidos.
              </p>
              <input type="password" value={deletePassword} onChange={e => setDeletePassword(e.target.value)} placeholder="Sua senha" className="input-field w-full" />
              <input value={deleteConfirm} onChange={e => setDeleteConfirm(e.target.value)} placeholder='Digite EXCLUIR para confirmar' className="input-field w-full" />
              <div className="flex gap-2">
                <button onClick={handleDeleteAccount} disabled={deleteConfirm !== 'EXCLUIR'} className="px-4 py-2 text-xs bg-[#E74C3C] text-white rounded-full disabled:opacity-50">
                  Confirmar exclusao permanente
                </button>
                <button onClick={() => setShowDelete(false)} className="text-muted text-xs">Cancelar</button>
              </div>
            </div>
          )}
        </div>

        <p className="text-muted text-xs text-center pb-8">
          <Link href="/privacidade" className="text-gold hover:underline">Politica de Privacidade</Link>
          {' · '}
          <Link href="/termos" className="text-gold hover:underline">Termos de Uso</Link>
          {' · '}
          <Link href="/support" className="text-gold hover:underline">Suporte</Link>
        </p>
      </div>
    </main>
  )
}
