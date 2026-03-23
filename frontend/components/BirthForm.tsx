'use client'

import { useState, FormEvent } from 'react'
import { motion } from 'framer-motion'

interface BirthFormData {
  name: string
  year: number
  month: number
  day: number
  hour: number
  minute: number
  city: string
  country: string
}

interface Props {
  onSubmit: (data: BirthFormData) => void
  loading: boolean
}

export default function BirthForm({ onSubmit, loading }: Props) {
  const [name, setName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [birthTime, setBirthTime] = useState('')
  const [unknownTime, setUnknownTime] = useState(false)
  const [city, setCity] = useState('')
  const [country, setCountry] = useState('')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!name || !birthDate || !city) return

    const [year, month, day] = birthDate.split('-').map(Number)
    let hour = 12
    let minute = 0

    if (!unknownTime && birthTime) {
      const [h, m] = birthTime.split(':').map(Number)
      hour = h
      minute = m
    }

    onSubmit({ name, year, month, day, hour, minute, city, country })
  }

  return (
    <motion.form
      onSubmit={handleSubmit}
      className="glass-card p-8 sm:p-10 w-full max-w-md mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <h2 className="font-display text-2xl font-light text-stardust text-center mb-8">
        Seus dados de nascimento
      </h2>

      <div className="space-y-5">
        {/* Name */}
        <div>
          <label className="block text-sm text-muted mb-2">Nome completo</label>
          <input
            type="text"
            className="input-field"
            placeholder="Seu nome"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        {/* Birth date */}
        <div>
          <label className="block text-sm text-muted mb-2">Data de nascimento</label>
          <input
            type="date"
            className="input-field"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            required
          />
        </div>

        {/* Birth time */}
        <div>
          <label className="block text-sm text-muted mb-2">Hora de nascimento</label>
          <input
            type="time"
            className="input-field"
            value={birthTime}
            onChange={(e) => setBirthTime(e.target.value)}
            disabled={unknownTime}
          />
          <label className="flex items-center gap-2 mt-2 cursor-pointer">
            <input
              type="checkbox"
              checked={unknownTime}
              onChange={(e) => setUnknownTime(e.target.checked)}
              className="rounded border-gold/30 bg-surface text-gold focus:ring-gold/30"
            />
            <span className="text-sm text-muted">Nao sei minha hora exata</span>
          </label>
        </div>

        {/* City */}
        <div>
          <label className="block text-sm text-muted mb-2">Cidade de nascimento</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ex: Sao Paulo, Brasil"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
          />
        </div>

        {/* Country */}
        <div>
          <label className="block text-sm text-muted mb-2">
            Pais <span className="text-muted/50">(opcional)</span>
          </label>
          <input
            type="text"
            className="input-field"
            placeholder="Ex: Brasil"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="btn-primary w-full mt-8 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12" cy="12" r="10"
                stroke="currentColor" strokeWidth="4" fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Consultando os astros...
          </span>
        ) : (
          'Calcular meu mapa \u2192'
        )}
      </button>
    </motion.form>
  )
}
