import { useCallback, useMemo, useState } from 'react'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import QueryBar, { QueryPayload } from './components/QueryBar'
import ChatMessage from './components/ChatMessage'
import SourcePanel from './components/SourcePanel'

export default function App() {
  const [messages, setMessages] = useState<any[]>([])
  const [sources, setSources] = useState<any[]>([])
  const [jobId, setJobId] = useState<string | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [markdown, setMarkdown] = useState('')
  const [error, setError] = useState<string | null>(null)

  const runAgent = useCallback(async (payload: QueryPayload) => {
    setIsRunning(true)
    setError(null)
    setMessages([])
    setSources([])
    setMarkdown('')
    setJobId(null)

    await fetchEventSource('/api/agent/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      onopen(response) {
        if (!response.ok) {
          setError('No se pudo iniciar el agente.')
          setIsRunning(false)
        }
      },
      onmessage(ev) {
        if (ev.event === 'done') {
          setIsRunning(false)
          return
        }
        if (ev.event === 'job') {
          try {
            const data = JSON.parse(ev.data)
            if (data.jobId) {
              setJobId(data.jobId)
            }
          } catch (err) {
            console.error('Error parsing job event', err)
          }
          return
        }
        if (!ev.data) return
        try {
          const state = JSON.parse(ev.data)
          if (state.messages) {
            setMessages(state.messages)
          }
          if (state.citations) {
            setSources(state.citations)
          }
          if (state.markdown) {
            setMarkdown(state.markdown)
          }
        } catch (err) {
          console.error('Error parsing state event', err)
        }
      },
      onerror(err) {
        console.error('SSE error', err)
        setError('Ocurrió un error durante la ejecución del agente.')
        setIsRunning(false)
      },
      openWhenHidden: true
    })
  }, [])

  const handleDownload = useCallback(async () => {
    if (!jobId) return
    const res = await fetch(`/api/report/${jobId}?format=markdown`)
    if (!res.ok) {
      setError('No fue posible descargar el reporte.')
      return
    }
    const text = await res.text()
    const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `reporte-${jobId}.md`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }, [jobId])

  const secondaryMessage = useMemo(() => {
    if (error) return error
    if (isRunning) return 'Generando reporte...'
    return 'Introduce uno o más tickers para comenzar.'
  }, [error, isRunning])

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b border-neutral-200">
        <div className="max-w-6xl mx-auto p-4 flex flex-col gap-3">
          <QueryBar onSubmit={runAgent} isRunning={isRunning} />
          <p className="text-sm text-neutral-500">{secondaryMessage}</p>
        </div>
      </header>
      <main className="max-w-6xl mx-auto grid md:grid-cols-[2fr_1fr] gap-6 p-4">
        <section className="space-y-4">
          {messages.length === 0 && (
            <div className="rounded-lg border border-dashed border-neutral-300 bg-white p-8 text-neutral-500">
              Aún no hay mensajes. Ejecuta una consulta para ver el análisis.
            </div>
          )}
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} role={msg.role} content={msg.content} />
          ))}
          {markdown && (
            <div className="rounded-lg border bg-white p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold">Reporte completo</h2>
                <button
                  onClick={handleDownload}
                  disabled={!jobId}
                  className="rounded-md border border-neutral-300 px-3 py-1 text-sm font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-50"
                >
                  Descargar Markdown
                </button>
              </div>
              <ChatMessage role="report" content={markdown} />
            </div>
          )}
        </section>
        <aside className="space-y-3">
          <SourcePanel sources={sources} />
          <div className="rounded-lg border bg-white p-4 text-xs text-neutral-500">
            <p>
              Este panel es informativo y no constituye asesoría financiera.
            </p>
          </div>
        </aside>
      </main>
    </div>
  )
}
