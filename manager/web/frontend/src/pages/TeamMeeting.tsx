import { useEffect, useState } from 'react'
import { CheckCircle2, MessageSquare, ShieldAlert, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { TeamMeetingContext, TeamMeetingResult } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

const effectLabels: Record<string, string> = {
  morale: 'Moral',
  cohesion: 'Cohesión',
  board: 'Junta',
  fan: 'Afición',
  relationship: 'Relación',
  prep_bonus: 'Preparación',
}

function effectText(effects: Record<string, number>) {
  return Object.entries(effects)
    .filter(([, value]) => Number(value) !== 0)
    .map(([key, value]) => `${effectLabels[key] || key} ${Number(value) > 0 ? '+' : ''}${value}`)
    .join(' · ')
}

export default function TeamMeetingPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<TeamMeetingContext | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [meetingType, setMeetingType] = useState('pre_match')
  const [tone, setTone] = useState('serena')
  const [topics, setTopics] = useState<string[]>(['objetivo'])
  const [promisePlayer, setPromisePlayer] = useState('')
  const [promiseType, setPromiseType] = useState('minutes')
  const [result, setResult] = useState<TeamMeetingResult | null>(null)

  function load() {
    setLoading(true)
    api.get<TeamMeetingContext>('/team-meeting')
      .then(({ data }) => {
        setData(data)
        setMeetingType(data.recommended_type || 'pre_match')
        setResult(null)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la reunión.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  function toggleTopic(topic: string) {
    setTopics((current) => current.includes(topic) ? current.filter((item) => item !== topic) : (current.length >= 3 ? current : [...current, topic]))
  }

  async function submit() {
    setBusy(true)
    try {
      const response = await api.post<{ result: TeamMeetingResult; meeting: TeamMeetingContext; state: unknown }>('/team-meeting', {
        meeting_type: meetingType,
        tone,
        topics,
        promise_player_id: promisePlayer,
        promise_type: promiseType,
      })
      setData(response.data.meeting)
      setResult(response.data.result)
      applyState(response.data.state as never)
      toast(response.message || 'Reunión celebrada.', response.data.result.success ? 'success' : 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo celebrar la reunión.', 'danger')
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <LoadingBlock label="Reuniendo al grupo…" />
  if (!data) return <Card><p className="muted">No se pudo cargar la reunión.</p></Card>

  const dynamics = data.dynamics

  return (
    <>
      <PageHeader
        eyebrow="Vestuario · liderazgo · promesas"
        title="Reunión de equipo"
        subtitle="Habla con el grupo, mueve la moral y la cohesión, y deja promesas que se comprobarán en las próximas semanas."
        actions={<Badge tone={dynamics.warnings.length ? 'warn' : 'ok'}>{dynamics.warnings.length ? 'Atención' : 'Grupo estable'}</Badge>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Moral" value={`${dynamics.morale}/20`} hint={dynamics.morale_label} tone={dynamics.morale >= 12 ? 'ok' : 'danger'} icon={Users} />
        <StatCard label="Cohesión" value={`${dynamics.cohesion}/20`} hint={dynamics.cohesion_label} tone={dynamics.cohesion >= 12 ? 'ok' : 'danger'} />
        <StatCard label="Junta" value={`${dynamics.board_confidence}/100`} hint={dynamics.board_label} tone="gold" icon={ShieldAlert} />
        <StatCard label="Promesas abiertas" value={dynamics.open_promises} hint={`Relación media ${dynamics.avg_relationship}`} tone="blue" icon={MessageSquare} />
      </div>

      {dynamics.warnings.length > 0 && (
        <Card className="mt-2">
          <div className="cat">AVISOS DEL VESTUARIO</div>
          {dynamics.warnings.map((warning) => <p className="small muted" key={warning}>{warning}</p>)}
        </Card>
      )}

      <div className="split-2 mt-2">
        <Card>
          <div className="cat">CONTEXTO</div>
          <h3 style={{ margin: '3px 0 0' }}>{data.next_fixture ? `${data.next_fixture.home_name} vs ${data.next_fixture.away_name}` : 'Sin próximo partido'}</h3>
          {data.next_fixture && <p className="small muted">J{data.next_fixture.round} · {dateLabel(data.next_fixture.date)}</p>}
          {data.last_result && <p className="small muted">Último partido: {data.last_result.result} {data.last_result.score} contra {data.last_result.rival} · {dateLabel(data.last_result.date)}</p>}
        </Card>
        <Card>
          <div className="cat">DINÁMICA</div>
          <div className="team-meeting-bars mt-1">
            <div><span>Moral</span><Progress value={dynamics.morale * 5} tone={dynamics.morale >= 12 ? 'ok' : 'danger'} /></div>
            <div><span>Cohesión</span><Progress value={dynamics.cohesion * 5} tone={dynamics.cohesion >= 12 ? 'ok' : 'danger'} /></div>
            <div><span>Junta</span><Progress value={dynamics.board_confidence} tone="gold" /></div>
            <div><span>Afición</span><Progress value={dynamics.fan_confidence} tone="blue" /></div>
          </div>
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">CONVOCAR REUNIÓN</div><h3 style={{ margin: '3px 0 0' }}>Mensaje y plan</h3></div>
          <MessageSquare size={20} className="gold" />
        </div>
        <div className="team-meeting-form mt-2">
          <Field label="Tipo de reunión"><select value={meetingType} onChange={(event) => setMeetingType(event.target.value)}>{data.meeting_types.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></Field>
          <Field label="Tono"><select value={tone} onChange={(event) => setTone(event.target.value)}>{data.tones.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></Field>
          <Field label="Jugador para promesa (opcional)"><select value={promisePlayer} onChange={(event) => setPromisePlayer(event.target.value)}><option value="">Sin promesa</option>{data.players.map((player) => <option key={player.id} value={player.id}>{player.name} · {player.position} · relación {player.relationship}</option>)}</select></Field>
          <Field label="Tipo de promesa"><select value={promiseType} onChange={(event) => setPromiseType(event.target.value)} disabled={!promisePlayer}>{data.promise_types.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></Field>
        </div>
        <div className="team-meeting-topics mt-2">
          {data.topics.map((topic) => (
            <label className={`team-meeting-topic ${topics.includes(topic.id) ? 'selected' : ''}`} key={topic.id}>
              <input type="checkbox" checked={topics.includes(topic.id)} onChange={() => toggleTopic(topic.id)} />
              <span><b>{topic.label}</b><small>{topic.description}</small></span>
            </label>
          ))}
        </div>
        <p className="small muted mt-1">Máximo tres temas. La promesa queda registrada y se comprobará en la fecha indicada.</p>
        <div className="actions mt-2"><Button variant="primary" icon={MessageSquare} onClick={submit} loading={busy} data-testid="team-meeting-submit">Convocar reunión</Button></div>
      </Card>

      {result && (
        <Card className={`mt-2 team-meeting-result ${result.success ? 'success' : 'failure'}`}>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">RESULTADO</div><h3 style={{ margin: '3px 0 0' }}>{result.success ? 'El mensaje ha calado' : 'El mensaje no ha calado'}</h3></div>
            <Badge tone={result.success ? 'ok' : 'danger'}>{result.success ? <CheckCircle2 size={12} /> : null}{result.success ? 'Éxito' : 'Sin efecto'}</Badge>
          </div>
          <p className="small muted mt-1">{result.message}</p>
          {effectText(result.effects) && <p className="small gold">{effectText(result.effects)}</p>}
          {result.promise && <p className="small muted">Promesa registrada para {result.meeting.promise_player}.</p>}
        </Card>
      )}

      <Card className="mt-2">
        <h3>Historial de reuniones</h3>
        <div className="stack-sm mt-2">
          {data.history.map((meeting) => (
            <div className="team-meeting-history-row" key={meeting.id}>
              <Badge tone={meeting.success ? 'ok' : 'danger'}>{meeting.success ? 'Conectó' : 'No conectó'}</Badge>
              <div><b>{meeting.type_label} · {meeting.tone_label}</b><span>{dateLabel(meeting.date)} · {meeting.topic_labels.join(' · ') || 'Sin temas'}</span></div>
              <span className="small muted">{effectText(meeting.effects)}</span>
            </div>
          ))}
          {!data.history.length && <p className="small muted">Todavía no has convocado ninguna reunión.</p>}
        </div>
      </Card>
    </>
  )
}
