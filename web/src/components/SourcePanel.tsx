interface SourceRef {
  kind: string
  title: string
  url: string
  meta?: Record<string, string>
}

interface Props {
  sources: SourceRef[]
}

export default function SourcePanel({ sources }: Props) {
  if (!sources || sources.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-neutral-300 bg-white p-4 text-sm text-neutral-500">
        Las fuentes aparecerán aquí cuando el agente obtenga documentos de la SEC o Yahoo Finance.
      </div>
    )
  }

  return (
    <div className="rounded-lg border bg-white p-4">
      <h2 className="text-sm font-semibold text-neutral-700 mb-3">Fuentes</h2>
      <ul className="space-y-2 text-sm">
        {sources.map((source, idx) => (
          <li key={`${source.url}-${idx}`} className="flex items-start gap-2">
            <span className="mt-0.5 rounded-full bg-neutral-200 px-2 py-0.5 text-xs uppercase text-neutral-600">
              {source.kind}
            </span>
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="text-brand hover:underline"
            >
              {source.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
}
