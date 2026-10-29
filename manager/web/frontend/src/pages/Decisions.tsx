import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, CheckCircle2, Clock3, History, ListChecks } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { EventHistoryItem, GameState, PendingDecision } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, EmptyState, LoadingBlock, PageHeader } from '../components/ui'

interface DecisionsPayload {
  pending: PendingDecision[]
  history: EventHistoryItem[]
}

export default function DecisionsPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<DecisionsPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<DecisionsPayload>('/events')
      setData(data)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudieron cargar las decisiones.', 'danger')
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => { void load() }, [load])

  async function decide(instanceId: string, choiceId: string) {
    setBusy(instanceId)
    try {
      const response = await api.post<{ state: GameState }>(`/events/${instanceId}`, { choice: choiceId })
      applyState(response.data.state)
      toast(response.message || 'Decisión tomada.', 'success')
      await load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo resolver la decisión.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Cargando decisiones…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar las decisiones.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Club · decisiones"
        title="Decisiones"
        subtitle="Todo lo que el club espera de ti: lesiones, vestuario, junta, mercado y prensa. Cada elección deja consecuencias."
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button>}
      />

      <div className="dashboard-kpis">
        <div className="stat-card"><span className="stat-top">PENDIENTES</span><strong>{data.pending.length}</strong><small>Decisiones abiertas</small></div>
        <div className="stat-card"><span className="stat-top">RESUELTAS</span><strong>{data.history.filter((item) => item.status === 'resolved').length}</strong><small>En el historial</small></div>
        <div className="stat-card"><span className="stat-top">CADUCADAS</span><strong>{data.history.filter((item) => item.status === 'expired').length}</strong><small>Decisiones que pasaron</small></div>
        <div className="stat-card"><span className="stat-top">CRÍTICAS</span><strong>{data.pending.filter((item) => item.priority >= 8).length}</strong><small>Prioridad alta</small></div>
      </div>

      {data.pending.length ? (
        <div className="stack-sm">
          {data.pending.map((decision) => (
            <Card className="decision-item" key={decision.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <div className="inline">
                  <Badge tone={decision.priority >= 8 ? 'danger' : 'neutral'}>{decision.category}</Badge>
                  <span className="small muted"><Clock3 size={12} /> Caduca {dateLabel(decision.expires_at)}</span>
                </div>
                <Badge tone={decision.priority >= 8 ? 'danger' : 'gold'}>Prioridad {decision.priority}/10</Badge>
              </div>
              <h2>{decision.title}</h2>
              <p>{decision.body}</p>
              <div className="decision-options">
                {decision.choices.map((choice) => (
                  <div className="decision-option" key={choice.id}>
                    <Button
                      size="sm"
                      variant={choice.tone === 'danger' ? 'danger' : choice.tone === 'ok' ? 'primary' : 'secondary'}
                      onClick={() => decide(decision.id, choice.id)}
                      loading={busy === decision.id}
                    >
                      {choice.label}
                    </Button>
                    {choice.description && <span>{choice.description}</span>}
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No hay decisiones pendientes"
          body="El club está en calma. Avanza el calendario y las historias aparecerán."
          action={<Button variant="primary" onClick={() => navigate('/game')}>Volver al dashboard</Button>}
        />
      )}

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div className="inline"><History size={16} /><h3 style={{ margin: 0 }}>Historial de decisiones</h3></div>
          <Badge tone="neutral">{data.history.length}</Badge>
        </div>
        {data.history.length ? (
          <div className="stack-sm mt-2">
            {data.history.map((item) => {
              const resolved = item.status === 'resolved'
              const label = resolved ? 'Resuelta' : item.status === 'expired' ? 'Caducada' : item.status === 'walked' ? 'Retirada' : 'Rechazada'
              return (
                <div className="decision-history-row" key={item.id}>
                  <span className={`decision-history-icon ${resolved ? 'ok' : 'warn'}`}>
                    {resolved ? <CheckCircle2 size={16} /> : <ListChecks size={16} />}
                  </span>
                  <div>
                    <div className="inline">
                      <b>{item.title}</b>
                      <Badge tone={resolved ? 'ok' : 'warn'}>{label}</Badge>
                    </div>
                    <span className="small muted">{item.category} · {dateLabel(item.date)}{item.choice_label ? ` · ${item.choice_label}` : ''}</span>
                    {item.response && <p className="small muted">{item.response}</p>}
                  </div>
                </div>
              )
            })}
          </div>
        ) : <p className="small muted mt-2">Todavía no hay decisiones en el historial.</p>}
      </Card>
    </>
  )
}
