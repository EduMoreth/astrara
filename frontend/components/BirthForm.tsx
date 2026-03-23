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

const COUNTRIES = [
  'Brasil',
  'África do Sul',
  'Alemanha',
  'Angola',
  'Argentina',
  'Austrália',
  'Bolívia',
  'Canadá',
  'Chile',
  'China',
  'Colômbia',
  'Coreia do Sul',
  'Cuba',
  'Equador',
  'Espanha',
  'Estados Unidos',
  'França',
  'Índia',
  'Irlanda',
  'Israel',
  'Itália',
  'Japão',
  'México',
  'Moçambique',
  'Nigéria',
  'Noruega',
  'Nova Zelândia',
  'Paraguai',
  'Peru',
  'Portugal',
  'Reino Unido',
  'Rússia',
  'Suécia',
  'Suíça',
  'Turquia',
  'Uruguai',
  'Venezuela',
]

const MONTHS = [
  { value: 1, label: 'Janeiro' },
  { value: 2, label: 'Fevereiro' },
  { value: 3, label: 'Março' },
  { value: 4, label: 'Abril' },
  { value: 5, label: 'Maio' },
  { value: 6, label: 'Junho' },
  { value: 7, label: 'Julho' },
  { value: 8, label: 'Agosto' },
  { value: 9, label: 'Setembro' },
  { value: 10, label: 'Outubro' },
  { value: 11, label: 'Novembro' },
  { value: 12, label: 'Dezembro' },
]

export default function BirthForm({ onSubmit, loading }: Props) {
  const [name, setName] = useState('')
  const [birthDay, setBirthDay] = useState('')
  const [birthMonth, setBirthMonth] = useState('')
  const [birthYear, setBirthYear] = useState('')
  const [birthTime, setBirthTime] = useState('')
  const [unknownTime, setUnknownTime] = useState(false)
  const [city, setCity] = useState('')
  const [country, setCountry] = useState('Brasil')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!name || !birthDay || !birthMonth || !birthYear || !city) return

    const day = parseInt(birthDay, 10)
    const month = parseInt(birthMonth, 10)
    const year = parseInt(birthYear, 10)

    if (isNaN(day) || isNaN(month) || isNaN(year)) return
    if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1900 || year > 2100) return

    let hour = 12
    let minute = 0

    if (!unknownTime && birthTime) {
      const [h, m] = birthTime.split(':').map(Number)
      hour = h
      minute = m
    }

    onSubmit({ name, year, month, day, hour, minute, city, country })
  }

  const currentYear = new Date().getFullYear()

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

        {/* Birth date - dd/mm/yyyy */}
        <div>
          <label className="block text-sm text-muted mb-2">Data de nascimento</label>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <input
                type="number"
                className="input-field text-center"
                placeholder="Dia"
                min={1}
                max={31}
                value={birthDay}
                onChange={(e) => setBirthDay(e.target.value)}
                required
              />
            </div>
            <div>
              <select
                className="input-field text-center"
                value={birthMonth}
                onChange={(e) => setBirthMonth(e.target.value)}
                required
              >
                <option value="">Mês</option>
                {MONTHS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <input
                type="number"
                className="input-field text-center"
                placeholder="Ano"
                min={1900}
                max={currentYear}
                value={birthYear}
                onChange={(e) => setBirthYear(e.target.value)}
                required
              />
            </div>
          </div>
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

        {/* Country - BEFORE city */}
        <div>
          <label className="block text-sm text-muted mb-2">País</label>
          <select
            className="input-field"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          >
            {COUNTRIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* City */}
        <div>
          <label className="block text-sm text-muted mb-2">Cidade de nascimento</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ex: São Paulo"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
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
