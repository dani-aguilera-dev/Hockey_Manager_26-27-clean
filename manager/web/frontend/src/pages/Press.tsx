import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Send } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { PressPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader } from '../components/ui'

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

  return (
    <>
      <PageHeader
        eyebrow="Sala de prensa"
        title="Rueda de prensa"
        subtitle="Cada respuesta deja titular y mueve la moral, la junta o la afición."
        actions={<Badge tone={data.done ? 'ok' : 'warn'}>{data.done ? 'Completada' : 'Pendiente'}</Badge>}
      />

      {data.context && (
        <Card className="mb-2">
          <div className="cat">DECLARACIONES DEL RIVAL · {data.context.rival}</div>
          <h3 style={{ margin: '4px 0' }}>{data.context.coach}</h3>
          <p className="press-quote">«{data.context.quote}»</p>
        </Card>
      )}

      {data.done ? (
        <>
          <Card>
            <h3>Rueda completada</h3>
            <div className="stack-sm">
              {data.history.slice().reverse().map((item, index) => (
                <div className="news-item" key={`${item.round}-${index}`}>
                  <div className="news-copy">
                    <div className="cat">J{item.round} · {item.opponent || 'Rueda de prensa'}</div>
                    <h3>{item.headline}</h3>
                    <p>{item.answer}</p>
                    {item.opponent_quote && <p className="small muted">Rival: «{item.opponent_quote}»</p>}
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <div className="actions mt-2"><Button variant="primary" onClick={() => navigate('/game')}>Volver al dashboard</Button></div>
        </>
      ) : (
        <>
          <div className="notice notice-info mb-2"><MessageSquare size={16} /><div>Habla el entrenador. La prensa espera. Tus palabras pueden proteger al grupo o aumentar la presión.</div></div>
          <div className="press-grid">
            {data.questions.map((question, index) => (
              <Card key={question.id} className="press-question">
                <div className="cat">PREGUNTA {index + 1}</div>
                <h3>{question.question}</h3>
                <div className="option-list">
                  {question.options.map((option, optionIndex) => (
                    <label className={`option-card ${answers[question.id] === optionIndex ? 'selected' : ''}`} key={option.label}>
                      <input type="radio" name={question.id} checked={answers[question.id] === optionIndex} onChange={() => setAnswers({ ...answers, [question.id]: optionIndex })} />
                      <span><b>{option.label}</b><br /><span>{option.headline}</span></span>
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
