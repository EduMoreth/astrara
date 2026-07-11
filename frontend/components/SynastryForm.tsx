'use client'

import { useState, useEffect, useRef, FormEvent } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

export interface SynastryPersonData {
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
  onSubmit: (personA: SynastryPersonData, personB: SynastryPersonData) => void
  loading: boolean
}

interface CityResult {
  city: string
  state: string
  country: string
  display: string
  lat: number
  lng: number
  tz_str: string
}

const COUNTRIES = [
  'Brasil', 'Africa do Sul', 'Alemanha', 'Angola', 'Argentina', 'Australia',
  'Bolivia', 'Canada', 'Chile', 'China', 'Colombia', 'Coreia do Sul', 'Cuba',
  'Equador', 'Espanha', 'Estados Unidos', 'Franca', 'India', 'Irlanda',
  'Israel', 'Italia', 'Japao', 'Mexico', 'Mocambique', 'Nigeria', 'Noruega',
  'Nova Zelandia', 'Paraguai', 'Peru', 'Portugal', 'Reino Unido', 'Russia',
  'Suecia', 'Suica', 'Turquia', 'Uruguai', 'Venezuela',
]

const MONTHS = [
  { value: 1, label: 'Janeiro' }, { value: 2, label: 'Fevereiro' },
  { value: 3, label: 'Marco' }, { value: 4, label: 'Abril' },
  { value: 5, label: 'Maio' }, { value: 6, label: 'Junho' },
  { value: 7, label: 'Julho' }, { value: 8, label: 'Agosto' },
  { value: 9, label: 'Setembro' }, { value: 10, label: 'Outubro' },
  { value: 11, label: 'Novembro' }, { value: 12, label: 'Dezembro' },
]

interface PersonState {
  name: string
  birthDay: string
  birthMonth: string
  birthYear: string
  birthTime: string
  unknownTime: boolean
  country: string
  cityQuery: string
  selectedCity: CityResult | null
}

const emptyPerson = (): PersonState => ({
  name: '', birthDay: '', birthMonth: '', birthYear: '', birthTime: '',
  unknownTime: false, country: 'Brasil', cityQuery: '', selectedCity: null,
})

/** One person's fieldset with its own city-autocomplete state. */
function PersonFields({ label, person, onChange }: {
  label: string
  person: PersonState
  onChange: (p: PersonState) => void
}) {
  const [cityResults, setCityResults] = useState<CityResult[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [searching, setSearching] = useState(false)
  const cityRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<NodeJS.Timeout | undefined>(undefined)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (cityRef.current && !cityRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (person.cityQuery.length < 2 || person.selectedCity) {
      setCityResults([])
      setShowDropdown(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await fetch(`${API_URL}/chart/search-city?q=${encodeURIComponent(person.cityQuery)}&country=${encodeURIComponent(person.country)}`)
        if (res.ok) {
          const data = await res.json()
          const list = Array.isArray(data) ? data : []
          setCityResults(list)
          setShowDropdown(list.length > 0)
        }
      } catch { /* silently fail */ } finally {
        setSearching(false)
      }
    }, 400)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [person.cityQuery, person.country, person.selectedCity])

  const set = (patch: Partial<PersonState>) => onChange({ ...person, ...patch })
  const currentYear = new Date().getFullYear()

  return (
    <div className="space-y-4">
      <h3 className="font-display text-lg text-gold">{label}</h3>

      <div>
        <label className="block text-sm text-muted mb-2">Nome</label>
        <input type="text" className="input-field" placeholder="Nome"
          value={person.name} onChange={(e) => set({ name: e.target.value })} required />
      </div>

      <div>
        <label className="block text-sm text-muted mb-2">Data de nascimento</label>
        <div className="grid grid-cols-3 gap-2">
          <input type="number" className="input-field text-center" placeholder="Dia"
            min={1} max={31} value={person.birthDay}
            onChange={(e) => set({ birthDay: e.target.value })} required />
          <select className="input-field text-center" value={person.birthMonth}
            onChange={(e) => set({ birthMonth: e.target.value })} required>
            <option value="">Mes</option>
            {MONTHS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
          <input type="number" className="input-field text-center" placeholder="Ano"
            min={1900} max={currentYear} value={person.birthYear}
            onChange={(e) => set({ birthYear: e.target.value })} required />
        </div>
      </div>

      <div>
        <label className="block text-sm text-muted mb-2">Hora de nascimento</label>
        <input type="time" className="input-field" value={person.birthTime}
          onChange={(e) => set({ birthTime: e.target.value })} disabled={person.unknownTime} />
        <label className="flex items-center gap-2 mt-2 text-xs text-muted cursor-pointer">
          <input type="checkbox" checked={person.unknownTime}
            onChange={(e) => set({ unknownTime: e.target.checked })} />
          Nao sei a hora (usar 12:00)
        </label>
      </div>

      <div>
        <label className="block text-sm text-muted mb-2">Pais</label>
        <select className="input-field" value={person.country}
          onChange={(e) => set({ country: e.target.value, selectedCity: null, cityQuery: '' })}>
          {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div ref={cityRef} className="relative">
        <label className="block text-sm text-muted mb-2">Cidade de nascimento</label>
        <div className="relative">
          <input type="text" className="input-field" placeholder="Digite o nome da cidade..."
            value={person.cityQuery}
            onChange={(e) => set({ cityQuery: e.target.value, selectedCity: null })}
            onFocus={() => { if (cityResults.length > 0) setShowDropdown(true) }}
            required />
          {searching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="w-4 h-4 border-2 border-gold/40 border-t-gold rounded-full animate-spin" />
            </div>
          )}
          {person.selectedCity && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gold text-sm">✓</div>
          )}
        </div>

        {showDropdown && cityResults.length > 0 && (
          <div className="absolute z-30 mt-1 w-full glass-card border border-gold/20 rounded-lg overflow-hidden">
            {cityResults.map((city, i) => (
              <button key={i} type="button"
                onClick={() => { onChange({ ...person, selectedCity: city, cityQuery: city.display }); setShowDropdown(false); setCityResults([]) }}
                className="w-full text-left px-4 py-2.5 hover:bg-gold/10 transition-colors">
                <span className="text-stardust text-sm block">{city.city}</span>
                <span className="text-muted text-xs">{city.state}{city.state ? ', ' : ''}{city.country}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function validatePerson(p: PersonState, label: string): SynastryPersonData | null {
  if (!p.name || !p.birthDay || !p.birthMonth || !p.birthYear) {
    toast.error(`Preencha os dados de ${label}`)
    return null
  }
  if (!p.selectedCity && !p.cityQuery) {
    toast.error(`Informe a cidade de nascimento de ${label}`)
    return null
  }
  const day = parseInt(p.birthDay, 10)
  const month = parseInt(p.birthMonth, 10)
  const year = parseInt(p.birthYear, 10)
  if (isNaN(day) || isNaN(month) || isNaN(year) ||
      day < 1 || day > 31 || month < 1 || month > 12 || year < 1900 || year > 2100) {
    toast.error(`Data de nascimento invalida para ${label}`)
    return null
  }
  const composed = new Date(year, month - 1, day)
  if (composed.getFullYear() !== year || composed.getMonth() !== month - 1 || composed.getDate() !== day) {
    toast.error(`Data de nascimento invalida para ${label}`)
    return null
  }
  let hour = 12
  let minute = 0
  if (!p.unknownTime && p.birthTime) {
    const [h, m] = p.birthTime.split(':').map(Number)
    hour = Number.isFinite(h) ? h : 12
    minute = Number.isFinite(m) ? m : 0
  }
  return {
    name: p.name, year, month, day, hour, minute,
    city: p.selectedCity?.city || p.cityQuery,
    country: p.selectedCity?.country || p.country,
  }
}

export default function SynastryForm({ onSubmit, loading }: Props) {
  const [personA, setPersonA] = useState<PersonState>(emptyPerson())
  const [personB, setPersonB] = useState<PersonState>(emptyPerson())

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const a = validatePerson(personA, 'Pessoa 1')
    if (!a) return
    const b = validatePerson(personB, 'Pessoa 2')
    if (!b) return
    onSubmit(a, b)
  }

  return (
    <motion.form
      onSubmit={handleSubmit}
      className="glass-card p-6 sm:p-10 w-full max-w-4xl mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <h2 className="font-display text-2xl font-light text-stardust text-center mb-2">
        Sinastria — Compatibilidade Astral
      </h2>
      <p className="text-muted text-sm text-center mb-8">
        Informe os dados de nascimento das duas pessoas para calcular a afinidade entre os mapas.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-10">
        <PersonFields label="♥ Pessoa 1" person={personA} onChange={setPersonA} />
        <PersonFields label="♥ Pessoa 2" person={personB} onChange={setPersonB} />
      </div>

      <button type="submit" disabled={loading}
        className="btn-primary w-full mt-10 disabled:opacity-50 disabled:cursor-not-allowed">
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Calculando afinidades...
          </span>
        ) : 'Calcular sinastria'}
      </button>
    </motion.form>
  )
}
