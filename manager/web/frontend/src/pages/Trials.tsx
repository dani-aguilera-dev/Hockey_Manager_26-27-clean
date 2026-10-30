import { useEffect, useState } from 'react'
import { ClipboardCheck, Search, UserPlus, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { ActiveTrial, TrialCandidate, TrialsData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

const recommendationTones: Record<string, 'ok' | 'gold' | 'danger'> = {
  fichar: 'ok',
  seguir: 'gold',
  descartar: 'danger',
}

export default function TrialsPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<TrialsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [reported, setReported] = useState<string | null>(null)

  function load(search = '') {
    setLoading(true)
    api.get<TrialsData>(`/trials?q=${encodeURIComponent(search)}`)
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar las pruebas.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function invite(candidate: TrialCandidate) {
    setBusy(`invite-${candidate.id}`)
    try {
      const response = await api.post<{ trials: TrialsData; state: unknown }>('/trials', { player_id: candidate.id, days: 14 })
      setData(response.data.trials)
      applyState(response.data.state as never)
      toast(response.message || 'Prueba iniciada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo iniciar la prueba.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function end(trial: ActiveTrial) {
    setBusy(`end-${trial.trial_id}`)
    try {
      const response = await api.post<{ result: { trial: { player_name: string; report: { summary: string } } }; trials: TrialsData; state: unknown }>(`/trials/${trial.trial_id}/end`)
      setData(response.data.trials)
      applyState(response.data.state as never)
      setReported(response.data.result.trial.player_name)
      toast(response.data.result.trial.report.summary, 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo cerrar la prueba.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Organizando las pruebas…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar las pruebas.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Cantera · mercado · agentes libres"
        title="Período de prueba"
        subtitle="Invita a agentes libres a entrenar unos días. Al terminar recibirás un informe con recomendación de fichar, seguir o descartar."
        actions={<Badge tone="gold">{data.summary.active}/{data.summary.max_active} a prueba</Badge>}
      />

      <div className="dashboard-kpis">
        <StatCard label="A prueba" value={data.summary.active} hint={`Máximo ${data.summary.max_active}`} tone="blue" icon={Users} />
        <StatCard label="Agentes libres" value={data.summary.candidates} hint="Disponibles en el mercado" tone="gold" icon={Search} />
        <StatCard label="Informes" value={data.summary.completed} hint="Pruebas completadas" icon={ClipboardCheck} />
        <StatCard label="Recomendación" value={data.history[0]?.report?.recommendation_label || '—'} hint={data.history[0]?.player_name || 'Sin informes'} tone="ok" />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">PRUEBAS ACTIVAS</div><h3 style={{ margin: '3px 0 0' }}>Jugadores entrenando</h3></div>
          <Badge tone="blue">{data.active.length}</Badge>
        </div>
        <div className="stack-sm mt-2">
          {data.active.map((trial) => (
            <div className="trial-row" key={trial.trial_id}>
              <div className="trial-main">
                <div className="inline"><b>{trial.name}</b><Badge tone="neutral">{trial.position}</Badge><span className="small muted">{trial.age} años · OVR {trial.overall} / POT {trial.potential}</span></div>
                <span className="small muted">Hasta {dateLabel(trial.end)} · {trial.days_left} días restantes · valor {money(trial.value)}</span>
                <Progress value={trial.progress} tone="gold" />
              </div>
              <Button size="sm" variant="primary" icon={ClipboardCheck} onClick={() => end(trial)} loading={busy === `end-${trial.trial_id}`} data-testid={`trial-end-${trial.trial_id}`}>Cerrar prueba</Button>
            </div>
          ))}
          {!data.active.length && <p className="small muted">No hay jugadores a prueba. Invita a un agente libre desde la lista inferior.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">CANDIDATOS</div><h3 style={{ margin: '3px 0 0' }}>Agentes libres</h3></div>
          <div className="trial-search"><Field label="Buscar"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nombre…" onKeyDown={(event) => { if (event.key === 'Enter') load(query) }} /></Field><Button icon={Search} onClick={() => load(query)}>Buscar</Button></div>
        </div>
        <div className="trial-grid mt-2">
          {data.candidates.map((candidate) => (
            <div className="trial-card" key={candidate.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><Badge tone="neutral">{candidate.position}</Badge><b className="gold">{candidate.overall}</b></div>
              <h3>{candidate.name}</h3>
              <p className="small muted">{candidate.age} años · potencial {candidate.potential} · {candidate.origin_team || 'Agente libre'}</p>
              <span className="small muted">Valor {money(candidate.value)} · salario {money(candidate.salary)}</span>
              <Button size="sm" variant="primary" icon={UserPlus} onClick={() => invite(candidate)} loading={busy === `invite-${candidate.id}`} data-testid={`trial-invite-${candidate.id}`}>Invitar a prueba</Button>
            </div>
          ))}
          {!data.candidates.length && <p className="small muted">No hay agentes libres que encajen con la búsqueda.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <h3>Informes de prueba</h3>
        <div className="stack-sm mt-2">
          {data.history.map((entry) => (
            <div className="trial-report" key={entry.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <div className="inline"><b>{entry.player_name}</b><Badge tone={recommendationTones[entry.report.recommendation] || 'neutral'}>{entry.report.recommendation_label}</Badge></div>
                <b className="gold">{entry.report.score}/100</b>
              </div>
              <p className="small muted">{entry.report.summary}</p>
              <div className="trial-report-grid">
                <div><span>Encaje</span><b>{entry.report.fit >= 0 ? '+' : ''}{entry.report.fit}</b></div>
                <div><span>Margen</span><b>+{entry.report.growth}</b></div>
                <div><span>Fuertes</span><b>{entry.report.strengths.join(' · ') || '—'}</b></div>
                <div><span>Débiles</span><b>{entry.report.weaknesses.join(' · ') || '—'}</b></div>
              </div>
              <span className="small muted">Prueba {dateLabel(entry.start)} → {dateLabel(entry.completed || entry.end)}</span>
            </div>
          ))}
          {!data.history.length && <p className="small muted">Todavía no hay informes. Cierra una prueba para generarlo.</p>}
        </div>
        {reported && <Badge tone="ok" className="trial-completed">Informe generado: {reported}</Badge>}
      </Card>
    </>
  )
}
