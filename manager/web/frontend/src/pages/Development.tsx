import { useEffect, useState } from 'react'
import { GraduationCap, Save, Sparkles, Trash2, TrendingUp } from 'lucide-react'
import { api } from '../lib/api'
import type { DevelopmentData, DevelopmentPlayer } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

type Draft = { focus: string; intensity: string; notes: string }

export default function DevelopmentPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<DevelopmentData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [drafts, setDrafts] = useState<Record<string, Draft>>({})
  const [saved, setSaved] = useState(false)

  function load() {
    setLoading(true)
    api.get<DevelopmentData>('/development')
      .then(({ data }) => {
        setData(data)
        setDrafts(Object.fromEntries(data.players.map((player) => [player.player_id, {
          focus: player.focus || 'tecnica',
          intensity: player.intensity || 'normal',
          notes: player.notes || '',
        }])))
        setSaved(false)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el desarrollo.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function savePlan(player: DevelopmentPlayer) {
    const draft = drafts[player.player_id]
    if (!draft) return
    setBusy(player.player_id)
    try {
      const response = await api.post<{ development: DevelopmentData; state: unknown }>(`/development/${player.player_id}`, draft)
      setData(response.data.development)
      applyState(response.data.state as never)
      setSaved(true)
      toast(response.message || 'Plan guardado.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo guardar el plan.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function clearPlan(player: DevelopmentPlayer) {
    setBusy(`clear-${player.player_id}`)
    try {
      const response = await api.delete<{ development: DevelopmentData; state: unknown }>(`/development/${player.player_id}`)
      setData(response.data.development)
      applyState(response.data.state as never)
      toast(response.message || 'Plan retirado.', 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo retirar el plan.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Preparando los planes individuales…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el desarrollo.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Cantera y primer equipo · desarrollo individual"
        title="Desarrollo de jugadores"
        subtitle="Asigna un foco, una intensidad y un plan semanal. Cada cuatro sesiones el jugador mejora atributos concretos."
        actions={<>{saved && <Badge tone="ok" className="development-saved">Guardado</Badge>}<Button icon={TrendingUp} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Planes activos" value={data.active} hint={`${data.players.length} jugadores disponibles`} tone="blue" icon={Sparkles} />
        <StatCard label="Cantera con plan" value={data.youth_active} hint="Jóvenes en desarrollo" tone="gold" icon={GraduationCap} />
        <StatCard label="Progreso medio" value={`${data.average_progress}%`} hint="Planes activos" icon={TrendingUp} />
        <StatCard label="Sin plan" value={data.players.length - data.active} hint="Jugadores sin foco individual" tone="danger" />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">PLANES INDIVIDUALES</div><h3 style={{ margin: '3px 0 0' }}>Primer equipo y cantera</h3></div>
          <Badge tone="neutral">{data.players.length}</Badge>
        </div>
        <div className="development-grid mt-2">
          {data.players.map((player) => {
            const draft = drafts[player.player_id] || { focus: 'tecnica', intensity: 'normal', notes: '' }
            return (
              <div className={`development-card ${player.focus ? 'active' : ''}`} key={player.player_id}>
                <div className="inline" style={{ justifyContent: 'space-between' }}>
                  <Badge tone={player.is_youth ? 'gold' : 'neutral'}>{player.is_youth ? 'Cantera' : player.category}</Badge>
                  <span className="small muted">{player.overall} / {player.potential}</span>
                </div>
                <h3>{player.name}</h3>
                <p className="small muted">{player.position} · {player.age} años {player.focus ? `· ${player.focus_label}` : '· sin plan'}</p>
                {player.focus && <><Progress value={player.progress} tone="gold" /><span className="small muted">{player.sessions} sesiones · {player.progress}% · último: {player.last_gain || '—'}</span></>}
                <div className="development-form">
                  <Field label="Foco">
                    <select value={draft.focus} onChange={(event) => setDrafts({ ...drafts, [player.player_id]: { ...draft, focus: event.target.value } })} data-testid={`development-focus-${player.player_id}`}>
                      {data.focuses.map((focus) => <option key={focus.id} value={focus.id}>{focus.label}</option>)}
                    </select>
                  </Field>
                  <Field label="Intensidad">
                    <select value={draft.intensity} onChange={(event) => setDrafts({ ...drafts, [player.player_id]: { ...draft, intensity: event.target.value } })}>
                      {data.intensities.map((intensity) => <option key={intensity.id} value={intensity.id}>{intensity.label}</option>)}
                    </select>
                  </Field>
                </div>
                <Field label="Nota"><input value={draft.notes} onChange={(event) => setDrafts({ ...drafts, [player.player_id]: { ...draft, notes: event.target.value } })} placeholder="Objetivo del plan…" /></Field>
                <div className="actions">
                  <Button size="sm" variant="primary" icon={Save} onClick={() => savePlan(player)} loading={busy === player.player_id} data-testid={`development-save-${player.player_id}`}>Guardar plan</Button>
                  {player.focus && <Button size="sm" variant="ghost" icon={Trash2} onClick={() => clearPlan(player)} loading={busy === `clear-${player.player_id}`}>Retirar</Button>}
                </div>
              </div>
            )
          })}
        </div>
      </Card>
    </>
  )
}
