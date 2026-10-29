import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Compass, FileSearch, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { ScoutData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'
import ScoutPanel from './ScoutPanel'

export default function ScoutingPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<ScoutData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [scoutId, setScoutId] = useState('')
  const [competition, setCompetition] = useState('')
  const [position, setPosition] = useState('')
  const [maxAge, setMaxAge] = useState('')
  const [focus, setFocus] = useState('equilibrado')

  function load() {
    setLoading(true)
    api.get<ScoutData>('/scouting')
      .then(({ data }) => {
        setData(data)
        setScoutId((current) => current || data.assignment_options?.scouts[0]?.id || '')
        setCompetition((current) => current || data.assignment_options?.competitions[0]?.code || '')
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el ojeo.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function createAssignment() {
    if (!competition) return
    setBusy('create')
    try {
      const response = await api.post<{ scouting: ScoutData; state: unknown }>('/scouting/assignments', {
        scout_id: scoutId,
        competition,
        position,
        max_age: maxAge,
        focus,
      })
      setData(response.data.scouting)
      applyState(response.data.state as never)
      toast(response.message || 'Asignación creada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo crear la asignación.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function cancelAssignment(assignmentId: string) {
    setBusy(assignmentId)
    try {
      const response = await api.delete<{ scouting: ScoutData; state: unknown }>(`/scouting/assignments/${assignmentId}`)
      setData(response.data.scouting)
      applyState(response.data.state as never)
      toast(response.message || 'Asignación cancelada.', 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo cancelar la asignación.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Organizando la red de ojeadores…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el ojeo.</p></Card>

  const options = data.assignment_options
  const assignments = data.assignments || []
  const reports = data.reports || []

  return (
    <>
      <PageHeader
        eyebrow="Red de ojeadores · asignaciones · informes"
        title="Ojeo y asignaciones"
        subtitle="Envía a tus ojeadores a una competición concreta, define posición, edad y enfoque, y recibe informes con objetivos reales."
        actions={<><Badge tone="gold">{data.scout.rating}/100 confianza</Badge><Button icon={RefreshCw} onClick={load} loading={loading}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Ojeador principal" value={data.scout.name} hint={`${data.scout.confidence} · rango ${data.scout.range}`} tone="blue" icon={Compass} />
        <StatCard label="Asignaciones activas" value={assignments.length} hint={`Máximo ${options?.max_active || 3}`} tone="gold" icon={FileSearch} />
        <StatCard label="Informes" value={reports.length} hint="Últimos informes recibidos" />
        <StatCard label="Recomendaciones" value={data.recommendations.length} hint="Objetivos que encajan ahora" tone="ok" />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">NUEVA ASIGNACIÓN</div><h3 style={{ margin: '3px 0 0' }}>Planifica la búsqueda</h3></div>
          <Plus size={20} className="gold" />
        </div>
        <div className="scout-assignment-form mt-2">
          <Field label="Ojeador"><select value={scoutId} onChange={(event) => setScoutId(event.target.value)}>{(options?.scouts || []).map((scout) => <option key={scout.id} value={scout.id}>{scout.name} · {scout.rating}</option>)}</select></Field>
          <Field label="Competición"><select value={competition} onChange={(event) => setCompetition(event.target.value)}>{(options?.competitions || []).map((item) => <option key={item.code} value={item.code}>{item.name} · {item.country}</option>)}</select></Field>
          <Field label="Posición"><select value={position} onChange={(event) => setPosition(event.target.value)}>{(options?.positions || []).map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></Field>
          <Field label="Edad máxima"><input value={maxAge} onChange={(event) => setMaxAge(event.target.value.replace(/\D/g, ''))} placeholder="Sin límite" inputMode="numeric" /></Field>
          <Field label="Enfoque"><select value={focus} onChange={(event) => setFocus(event.target.value)}>{(options?.focuses || data.focuses).map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></Field>
          <Button variant="primary" icon={Plus} onClick={createAssignment} loading={busy === 'create'} disabled={!competition || assignments.length >= (options?.max_active || 3)} data-testid="scout-assignment-create">Crear asignación</Button>
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">ASIGNACIONES ACTIVAS</div><h3 style={{ margin: '3px 0 0' }}>Búsquedas en curso</h3></div>
          <Badge tone="blue">{assignments.length}</Badge>
        </div>
        <div className="stack-sm mt-2">
          {assignments.map((assignment) => (
            <div className="scout-assignment-row" key={assignment.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <div><b>{assignment.scout_name} · {assignment.competition_name}</b><span>{assignment.position || 'Todas las posiciones'} · {assignment.max_age ? `hasta ${assignment.max_age} años` : 'sin límite de edad'} · {assignment.focus_label}</span></div>
                <Badge tone="gold">{assignment.progress}%</Badge>
              </div>
              <Progress value={assignment.progress} tone="gold" />
              <div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Creada {dateLabel(assignment.created)} · {assignment.reports} informe(s)</span><Button size="sm" variant="ghost" icon={Trash2} onClick={() => cancelAssignment(assignment.id)} loading={busy === assignment.id}>Cancelar</Button></div>
            </div>
          ))}
          {!assignments.length && <p className="small muted">No hay asignaciones activas. Crea una para que la red trabaje en una competición concreta.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">INFORMES RECIBIDOS</div><h3 style={{ margin: '3px 0 0' }}>Últimos descubrimientos</h3></div>
          <Badge tone="neutral">{reports.length}</Badge>
        </div>
        <div className="stack-sm mt-2">
          {reports.map((report) => (
            <div className="scout-report" key={report.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><b>{report.competition_name} · {report.scout_name}</b><span className="small muted">{dateLabel(report.date)}</span></div>
              <p className="small muted">{report.message}</p>
              {report.players.map((player) => <button type="button" className="scout-report-player" key={player.id} onClick={() => navigate(`/game/player/${player.id}`)}><b>{player.name}</b><span>{player.team} · {player.age} años · OVR {player.overall} · fit {Math.round(player.score || 0)}</span></button>)}
            </div>
          ))}
          {!reports.length && <p className="small muted">Todavía no hay informes. Las asignaciones avanzan con las jornadas.</p>}
        </div>
      </Card>

      <ScoutPanel onUseMarket={() => navigate('/game/market')} />
    </>
  )
}
