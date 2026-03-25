'use client'

import { useState, useEffect, useRef, FormEvent } from 'react'
import { motion } from 'framer-motion'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

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

export default function BirthForm({ onSubmit, loading }: Props) {
  const [name, setName] = useState('')
  const [birthDay, setBirthDay] = useState('')
  const [birthMonth, setBirthMonth] = useState('')
  const [birthYear, setBirthYear] = useState('')
  const [birthTime, setBirthTime] = useState('')
  const [unknownTime, setUnknownTime] = useState(false)
  const [country, setCountry] = useState('Brasil')

  // City autocomplete state
  const [cityQuery, setCityQuery] = useState('')
  const [cityResults, setCityResults] = useState<CityResult[]>([])
  const [selectedCity, setSelectedCity] = useState<CityResult | null>(null)
  const [showCityDropdown, setShowCityDropdown] = useState(false)
  const [searchingCity, setSearchingCity] = useState(false)
  const cityRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<NodeJS.Timeout>()

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (cityRef.current && !cityRef.current.contains(e.target as Node)) {
        setShowCityDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Search cities with debounce
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (cityQuery.length < 2 || selectedCity) {
      setCityResults([])
      setShowCityDropdown(false)
      return
    }

    debounceRef.current = setTimeout(async () => {
      setSearchingCity(true)
      try {
        const res = await fetch(`${API_URL}/chart/search-city?q=${encodeURIComponent(cityQuery)}&country=${encodeURIComponent(country)}`)
        if (res.ok) {
          const data = await res.json()
          setCityResults(data)
          setShowCityDropdown(data.length > 0)
        }
      } catch {
        // silently fail
      } finally {
        setSearchingCity(false)
      }
    }, 400)

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [cityQuery, country, selectedCity])

  function selectCity(city: CityResult) {
    setSelectedCity(city)
    setCityQuery(city.display)
    setShowCityDropdown(false)
    setCityResults([])
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!name || !birthDay || !birthMonth || !birthYear) return

    // Must have selected a city from autocomplete
    if (!selectedCity) {
      // If user typed but didn't select, use raw text
      if (!cityQuery) return
    }

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

    onSubmit({
      name,
      year,
      month,
      day,
      hour,
      minute,
      city: selectedCity?.city || cityQuery,
      country: selectedCity?.country || country,
    })
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
          <div className="grid grid-cols-3 gap-2 sm:gap-3">
            <input
              type="number"
              className="input-field text-center"
              placeholder="Dia"
              min={1} max={31}
              value={birthDay}
              onChange={(e) => setBirthDay(e.target.value)}
              required
            />
            <select
              className="input-field text-center"
              value={birthMonth}
              onChange={(e) => setBirthMonth(e.target.value)}
              required
            >
              <option value="">Mes</option>
              {MONTHS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
            <input
              type="number"
              className="input-field text-center"
              placeholder="Ano"
              min={1900} max={currentYear}
              value={birthYear}
              onChange={(e) => setBirthYear(e.target.value)}
              required
            />
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
              className="accent-gold"
            />
            <span className="text-sm text-muted">Nao sei minha hora exata</span>
          </label>
        </div>

        {/* Country */}
        <div>
          <label className="block text-sm text-muted mb-2">Pais</label>
          <select
            className="input-field"
            value={country}
            onChange={(e) => { setCountry(e.target.value); setSelectedCity(null); setCityQuery('') }}
          >
            {COUNTRIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {/* City with autocomplete */}
        <div ref={cityRef} className="relative">
          <label className="block text-sm text-muted mb-2">Cidade de nascimento</label>
          <div className="relative">
            <input
              type="text"
              className="input-field pr-8"
              placeholder="Digite o nome da cidade..."
              value={cityQuery}
              onChange={(e) => {
                setCityQuery(e.target.value)
                if (selectedCity) setSelectedCity(null)
              }}
              onFocus={() => { if (cityResults.length > 0) setShowCityDropdown(true) }}
              required
            />
            {searchingCity && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <div className="w-4 h-4 border-2 border-gold border-t-transparent rounded-full animate-spin" />
              </div>
            )}
            {selectedCity && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[#2ECC71]">
                ✓
              </div>
            )}
          </div>

          {/* Autocomplete dropdown */}
          {showCityDropdown && cityResults.length > 0 && (
            <div className="absolute z-50 w-full mt-1 glass-card rounded-xl overflow-hidden border border-gold/20 shadow-lg max-h-48 overflow-y-auto">
              {cityResults.map((city, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => selectCity(city)}
                  className="w-full text-left px-4 py-3 hover:bg-surface-2 transition-colors border-b border-white/[0.03] last:border-0"
                >
                  <span className="text-stardust text-sm block">{city.city}</span>
                  <span className="text-muted text-xs">{city.state}{city.state ? ', ' : ''}{city.country}</span>
                </button>
              ))}
            </div>
          )}

          {selectedCity && (
            <p className="text-xs text-muted mt-1">
              📍 {selectedCity.display}
            </p>
          )}
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
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Consultando os astros...
          </span>
        ) : (
          'Calcular meu mapa →'
        )}
      </button>
    </motion.form>
  )
}
