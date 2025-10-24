import { FormEvent, useMemo, useState } from 'react'
import ToggleFilters from './ToggleFilters'

export interface QueryPayload {
  query: string
  companies: { ticker?: string; cik?: string }[]
  retrieval: {
    forms: string[]
    years: number[]
  }
}

interface Props {
  onSubmit: (payload: QueryPayload) => Promise<void>
  isRunning: boolean
}

const FORM_OPTIONS = ['10-K', '10-Q', '20-F']

export default function QueryBar({ onSubmit, isRunning }: Props) {
  const [query, setQuery] = useState('')
  const [tickers, setTickers] = useState('AAPL, MSFT')
  const [years, setYears] = useState('2022, 2023, 2024')
  const [selectedForms, setSelectedForms] = useState<string[]>(FORM_OPTIONS)

  const canSubmit = useMemo(() => {
    return tickers.trim().length > 0 && years.trim().length > 0 && selectedForms.length > 0
  }, [tickers, years, selectedForms])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!canSubmit) return
    const tickersList = tickers
      .split(',')
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean)
      .map((ticker) => ({ ticker }))
    const yearsList = years
      .split(',')
      .map((y) => parseInt(y.trim(), 10))
      .filter((y) => !Number.isNaN(y))
    await onSubmit({
      query,
      companies: tickersList,
      retrieval: {
        forms: selectedForms,
        years: yearsList
      }
    })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          placeholder="¿Qué deseas analizar?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 min-w-[200px] rounded-lg border border-neutral-300 bg-white px-4 py-2 text-sm shadow-sm focus:border-brand focus:outline-none"
        />
        <button
          type="submit"
          disabled={!canSubmit || isRunning}
          className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand/90 disabled:opacity-50"
        >
          {isRunning ? 'Generando…' : 'Analizar'}
        </button>
      </div>
      <div className="flex flex-wrap gap-4 text-sm text-neutral-600">
        <label className="flex items-center gap-2">
          <span className="text-neutral-500">Tickers</span>
          <input
            type="text"
            value={tickers}
            onChange={(e) => setTickers(e.target.value)}
            className="rounded-md border border-neutral-300 bg-white px-3 py-1 focus:border-brand focus:outline-none"
          />
        </label>
        <label className="flex items-center gap-2">
          <span className="text-neutral-500">Años</span>
          <input
            type="text"
            value={years}
            onChange={(e) => setYears(e.target.value)}
            className="rounded-md border border-neutral-300 bg-white px-3 py-1 focus:border-brand focus:outline-none"
          />
        </label>
        <ToggleFilters
          options={FORM_OPTIONS}
          value={selectedForms}
          onChange={setSelectedForms}
          label="Formas"
        />
      </div>
    </form>
  )
}
