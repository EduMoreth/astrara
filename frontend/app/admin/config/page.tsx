'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getConfig, updateConfig } from '@/lib/admin-api'

const AI_MODELS = ['claude-sonnet-4-6', 'claude-opus-4-6', 'claude-haiku-4-5-20251001']

export default function AdminConfigPage() {
  const [config, setConfig] = useState<Record<string, { value: string; description: string }>>({})
  const [edits, setEdits] = useState<Record<string, string>>({})

  useEffect(() => {
    getConfig().then(cfg => {
      setConfig(cfg)
      const initial: Record<string, string> = {}
      Object.entries(cfg).forEach(([k, v]) => { initial[k] = v.value })
      setEdits(initial)
    }).catch(() => toast.error('Erro ao carregar'))
  }, [])

  async function handleSave() {
    try {
      await updateConfig(edits)
      toast.success('Configuracoes salvas')
    } catch { toast.error('Erro ao salvar') }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-2xl text-stardust">Configuracoes</h2>
        <button onClick={handleSave} className="btn-primary text-sm">Salvar alteracoes</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(config).map(([key, { description }]) => (
          <div key={key} className="glass-card p-5">
            <label className="text-gold text-xs font-mono mb-1 block">{key}</label>
            <p className="text-muted text-xs mb-3">{description}</p>

            {key === 'ai_model' ? (
              <select
                value={edits[key] || ''}
                onChange={e => setEdits({ ...edits, [key]: e.target.value })}
                className="input-field w-full"
              >
                {AI_MODELS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            ) : key === 'maintenance_mode' ? (
              <button
                onClick={() => setEdits({ ...edits, [key]: edits[key] === 'true' ? 'false' : 'true' })}
                className={`w-12 h-6 rounded-full transition-colors ${edits[key] === 'true' ? 'bg-[#E74C3C]' : 'bg-[#2ECC71]'}`}
              >
                <div className={`w-5 h-5 rounded-full bg-white transition-transform ${edits[key] === 'true' ? 'translate-x-6' : 'translate-x-0.5'}`} />
              </button>
            ) : (
              <input
                value={edits[key] || ''}
                onChange={e => setEdits({ ...edits, [key]: e.target.value })}
                className="input-field w-full"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
