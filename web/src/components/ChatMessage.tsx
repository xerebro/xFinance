import ReactMarkdown from 'react-markdown'

interface Props {
  role: string
  content: string
}

const roleStyles: Record<string, string> = {
  system: 'bg-white border border-neutral-200',
  status: 'bg-blue-50 border border-blue-100 text-blue-900',
  final: 'bg-emerald-50 border border-emerald-100 text-emerald-900',
  report: 'bg-white border border-neutral-200',
  default: 'bg-white border border-neutral-200'
}

export default function ChatMessage({ role, content }: Props) {
  const style = roleStyles[role] ?? roleStyles.default
  const isMarkdown = role === 'report' || role === 'system'
  return (
    <article className={`rounded-lg p-4 shadow-sm ${style}`}>
      <div className="text-xs uppercase tracking-wide text-neutral-400 mb-2">{role}</div>
      {isMarkdown ? (
        <ReactMarkdown className="prose prose-sm max-w-none">{content}</ReactMarkdown>
      ) : (
        <p className="text-sm text-neutral-700 whitespace-pre-wrap">{content}</p>
      )}
    </article>
  )
}
