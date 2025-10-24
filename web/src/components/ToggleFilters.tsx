interface Props {
  options: string[]
  value: string[]
  onChange: (next: string[]) => void
  label?: string
}

export default function ToggleFilters({ options, value, onChange, label }: Props) {
  const toggle = (option: string) => {
    if (value.includes(option)) {
      onChange(value.filter((item) => item !== option))
    } else {
      onChange([...value, option])
    }
  }

  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-neutral-500">{label}</span>}
      <div className="flex gap-2">
        {options.map((option) => {
          const active = value.includes(option)
          return (
            <button
              type="button"
              key={option}
              onClick={() => toggle(option)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                active
                  ? 'border-brand bg-brand/10 text-brand'
                  : 'border-neutral-300 bg-white text-neutral-500 hover:border-brand/50'
              }`}
            >
              {option}
            </button>
          )
        })}
      </div>
    </div>
  )
}
