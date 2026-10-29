import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Newspaper, Radio, Send } from 'lucide-react'
import { api } from '../lib/api'
import type { PressPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, Progress } from '../components/ui'

const effectLabels: Record<string, string> = {
  morale: 'Moral',
  fan: 'Afición',
  board: 'Junta',
  cohesion: 'Cohesión',
  relationship: 'Relación',
  media: 'Prensa',
}

function effectText(effects: Record<string, number | string>) {
  return Object.entries(effects)
    .filter(([, value]) => Number(value) !== 0)
    .map(([key, value]) => `${effectLabels[key] || key} ${Number(value) > 0 ? '+' : ''}${value}`)
    .join(' · ')
}

export default function PressPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<PressPayload | null>(null)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)

  function load() {
    setLoading(true)
    api.get<PressPayload>('/press')
      .then(({ data }) => {
        setData(data)
        setAnswers(Object.fromEntries(data.questions.map((question) => [question.id, 0])))
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la rueda de prensa.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function submit() {
    setSending(true)
    try {
      const response = await api.post<{ state: unknown }>('/press', { answers })
      applyState(response.data.state as never)
      toast(response.message || 'Rueda de prensa completada.', 'success')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo enviar la rueda de prensa.', 'danger')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <LoadingBlock label="Preparando la sala de prensa…" />
  if (!data) return <Card><p className="muted">No se pudo cargar la rueda de prensa.</p></Card>

  const context = data.context
  const media = context.media_confidence ?? 50

  return (
    <>
      <PageHeader
        eyebrow="Sala de prensa · medios y vestuario"
        title="Rueda de prensa"
        subtitle="Cada respuesta deja titular y mueve moral, junta, afición, vestuario y confianza de los medios."
        actions={<><Badge tone={data.done ? 'ok' : 'warn'}>{data.done ? 'Completada' : 'Pendiente'}</Badge>{data.post_available && <Button icon={Newspaper} onClick={() => navigate('/game/press/post')}>Rueda posterior</Button>}</>}
      />

      {context && (
        <div className="press-context-grid">
          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}>
              <div className="cat">MEDIO ACREDITADO</div>
              <Badge tone="blue">{context.style || 'Prensa'}</Badge>
            </div>
            <div className="inline mt-1"><Newspaper size={20} className="gold" /><div><h3 style={{ margin: 0 }}>{context.outlet || 'Sala de prensa'}</h3><p className="small muted" style={{ margin: '2px 0 0' }}>{context.journalist || 'Periodista'}</p></div></div>
            <p className="small muted mt-2">{context.tone || 'La sala espera respuestas.'}</p>
          </Card>
          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}>
              <div className="cat">RELACIÓN CON LOS MEDIOS</div>
              <Badge tone={media >= 65 ? 'ok' : media >= 40 ? 'warn' : 'danger'}>{media}/100</Badge>
            </div>
            <p className="small muted mt-1">Una sala cómoda protege al grupo; una prensa hostil amplifica cualquier error.</p>
            <Progress value={media} tone={media >= 65 ? 'ok' : media >= 40 ? 'gold' : 'danger'} />
            <div className="inline mt-2"><Badge tone="neutral">Bias: {context.bias || 'equilibrado'}</Badge><Badge tone="neutral">Rival: {context.rival}</Badge></div>
          </Card>
          <Card>
            <div className="cat">DECLARACIONES DEL RIVAL</div>
            <h3 style={{ margin: '4px 0' }}>{context.coach}</h3>
            <p className="press-quote">«{context.quote}»</p>
          </Card>
        </div>
      )}

      {data.done ? (
        <>
          <Card className="mt-2">
            <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Lo que ha quedado</h3><Badge tone="ok">Rueda cerrada</Badge></div>
            <div className="stack-sm mt-2">
              {data.history.slice().reverse().map((item, index) => (
                <div className="news-item" key={`${item.round}-${index}`}>
                  <div className="news-copy">
                    <div className="cat">J{item.round} · {item.outlet || item.opponent || 'Rueda de prensa'}{item.journalist ? ` · ${item.journalist}` : ''}</div>
                    <h3>{item.headline}</h3>
                    <p>{item.answer}</p>
                    {item.opponent_quote && <p className="small muted">Rival: «{item.opponent_quote}»</p>}
                    {item.effects && <p className="small gold">{effectText(item.effects)}</p>}
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <div className="actions mt-2"><Button variant="primary" onClick={() => navigate('/game')}>Volver al dashboard</Button></div>
        </>
      ) : (
        <>
          <div className="notice notice-info mt-2"><MessageSquare size={16} /><div>Habla el entrenador. La prensa espera. Tus palabras pueden proteger al grupo, calentar al rival o aumentar la presión de la junta.</div></div>
          <div className="press-grid">
            {data.questions.map((question, index) => {
              const selected = question.options[answers[question.id] ?? 0]
              return (
                <Card key={question.id} className="press-question">
                  <div className="inline" style={{ justifyContent: 'space-between' }}><div className="cat">PREGUNTA {index + 1} · {question.topic || 'SALA'}</div><Radio size={16} className="muted" /></div>
                  <h3>{question.question}</h3>
                  <div className="option-list">
                    {question.options.map((option, optionIndex) => (
                      <label className={`option-card ${answers[question.id] === optionIndex ? 'selected' : ''}`} key={option.label}>
                        <input type="radio" name={question.id} checked={answers[question.id] === optionIndex} onChange={() => setAnswers({ ...answers, [question.id]: optionIndex })} />
                        <span><b>{option.label}</b><br /><span>{option.headline}</span>{effectText(option.effects) && <em className="press-effect">{effectText(option.effects)}</em>}</span>
                      </label>
                    ))}
                  </div>
                  {selected && <p className="press-followup">Titular probable: <b>{selected.headline}</b></p>}
                </Card>
              )
            })}
          </div>
          <div className="actions mt-2"><Button variant="primary" size="lg" icon={Send} onClick={submit} loading={sending}>Enviar respuestas</Button></div>
        </>
      )}
    </>
  )
}
