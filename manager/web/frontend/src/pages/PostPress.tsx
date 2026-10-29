import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Newspaper, Send } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { PostPressPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, Progress } from '../components/ui'

const effectLabels: Record<string, string> = {
  morale: 'Moral', fan: 'Afición', board: 'Junta', cohesion: 'Cohesión', relationship: 'Relación', media: 'Prensa',
}

function effectText(effects: Record<string, number | string>) {
  return Object.entries(effects)
    .filter(([, value]) => Number(value) !== 0)
    .map(([key, value]) => `${effectLabels[key] || key} ${Number(value) > 0 ? '+' : ''}${value}`)
    .join(' · ')
}

export default function PostPressPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<PostPressPayload | null>(null)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)

  function load() {
    setLoading(true)
    api.get<PostPressPayload>('/press/post')
      .then(({ data }) => {
        setData(data)
        setAnswers(Object.fromEntries(data.questions.map((question) => [question.id, 0])))
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No hay rueda posterior.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function submit() {
    setSending(true)
    try {
      const response = await api.post<{ state: unknown }>('/press/post', { answers })
      applyState(response.data.state as never)
      toast(response.message || 'Rueda posterior completada.', 'success')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo enviar la rueda posterior.', 'danger')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <LoadingBlock label="Preparando la rueda posterior…" />
  if (!data) return <Card><p className="muted">No hay rueda posterior disponible.</p><Button onClick={() => navigate('/game')}>Volver</Button></Card>

  const context = data.context
  const media = context.media_confidence ?? 50

  return (
    <>
      <PageHeader
        eyebrow="Post-partido · sala de prensa"
        title="La voz del vestuario"
        subtitle={`${context.result} · ${context.score} contra ${context.rival} · ${dateLabel(context.date)}`}
        actions={<Badge tone={data.done ? 'ok' : 'warn'}>{data.done ? 'Completada' : 'Pendiente'}</Badge>}
      />

      <div className="press-context-grid">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div className="cat">MEDIO ACREDITADO</div><Badge tone="blue">{context.style || 'Prensa'}</Badge></div>
          <div className="inline mt-1"><Newspaper size={20} className="gold" /><div><h3 style={{ margin: 0 }}>{context.outlet}</h3><p className="small muted" style={{ margin: '2px 0 0' }}>{context.journalist}</p></div></div>
          <p className="small muted mt-2">{context.tone}</p>
        </Card>
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div className="cat">CONFIANZA MEDIÁTICA</div><Badge tone={media >= 65 ? 'ok' : media >= 40 ? 'warn' : 'danger'}>{media}/100</Badge></div>
          <p className="small muted mt-1">La sala posterior puede proteger al grupo o abrir una crisis.</p>
          <Progress value={media} tone={media >= 65 ? 'ok' : media >= 40 ? 'gold' : 'danger'} />
        </Card>
        <Card>
          <div className="cat">RESULTADO</div>
          <div className="score-value" style={{ fontSize: 38, margin: '4px 0' }}>{context.score}</div>
          <p className="small muted">{context.result} contra {context.rival}</p>
        </Card>
      </div>

      {data.done ? (
        <Card className="mt-2">
          <h3>Rueda completada</h3>
          <div className="stack-sm mt-2">
            {data.history.slice().reverse().map((item, index) => (
              <div className="news-item" key={`${item.round}-${index}`}>
                <div className="news-copy"><div className="cat">Post-partido · {item.outlet || item.opponent}</div><h3>{item.headline}</h3><p>{item.answer}</p>{item.effects && <p className="small gold">{effectText(item.effects)}</p>}</div>
              </div>
            ))}
          </div>
          <div className="actions mt-2"><Button variant="primary" onClick={() => navigate('/game')}>Volver al dashboard</Button></div>
        </Card>
      ) : (
        <>
          <div className="notice notice-info mt-2"><MessageSquare size={16} /><div>Ahora habla el entrenador después del partido. Las respuestas pueden reforzar o erosionar la confianza del grupo y de la prensa.</div></div>
          <div className="press-grid">
            {data.questions.map((question, index) => (
              <Card key={question.id} className="press-question">
                <div className="cat">PREGUNTA {index + 1} · {question.topic || 'POST'}</div>
                <h3>{question.question}</h3>
                <div className="option-list">
                  {question.options.map((option, optionIndex) => (
                    <label className={`option-card ${answers[question.id] === optionIndex ? 'selected' : ''}`} key={option.label}>
                      <input type="radio" name={question.id} checked={answers[question.id] === optionIndex} onChange={() => setAnswers({ ...answers, [question.id]: optionIndex })} />
                      <span><b>{option.label}</b><br /><span>{option.headline}</span>{effectText(option.effects) && <em className="press-effect">{effectText(option.effects)}</em>}</span>
                    </label>
                  ))}
                </div>
              </Card>
            ))}
          </div>
          <div className="actions mt-2"><Button variant="primary" size="lg" icon={Send} onClick={submit} loading={sending}>Enviar respuestas</Button></div>
        </>
      )}
    </>
  )
}
