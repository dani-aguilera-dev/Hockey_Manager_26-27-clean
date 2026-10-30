import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, Search, Send, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { VacanciesData, Vacancy } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, StatCard } from '../components/ui'

export default function VacanciesPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<VacanciesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [result, setResult] = useState<string | null>(null)
  const [resultAccepted, setResultAccepted] = useState(false)

  function load() {
    setLoading(true)
    api.get<VacanciesData>('/vacancies')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar las vacantes.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function apply(vacancy: Vacancy) {
    setBusy(vacancy.id)
    try {
      const response = await api.post<{ result: { accepted: boolean; message: string }; vacancies: VacanciesData; state: unknown }>(`/vacancies/${vacancy.id}/apply`)
      setData(response.data.vacancies)
      applyState(response.data.state as never)
      setResult(response.data.result.message)
      setResultAccepted(response.data.result.accepted)
      toast(response.data.result.message, response.data.result.accepted ? 'success' : 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo presentar la candidatura.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Revisando el mercado de entrenadores…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar las vacantes.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Mercado de entrenadores · candidaturas · banquillos"
        title="Vacantes de entrenador"
        subtitle="Clubes con el banquillo en dificultades o vacante. Los clubes IA pueden destituir a su entrenador tras varias jornadas en la parte baja; si aceptan tu candidatura, se abre una oferta en Trabajo y seguridad."
        actions={<><Badge tone="gold">{data.summary.vacancies} vacantes</Badge><Button icon={Search} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Vacantes" value={data.summary.vacancies} hint="Clubes con banquillo disponible" tone="blue" icon={Briefcase} />
        <StatCard label="Candidaturas" value={data.summary.applications} hint="Enviadas en esta partida" tone="gold" icon={Send} />
        <StatCard label="Ofertas abiertas" value={data.summary.offers} hint="Candidaturas aceptadas" tone="ok" icon={Users} />
        <StatCard label="Mercado" value="Misma liga, España e internacional" hint="Cambio al aceptar la oferta" />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">BANQUILLOS DISPONIBLES</div><h3 style={{ margin: '3px 0 0' }}>Clubes que buscan entrenador</h3></div>
          <Badge tone="neutral">{data.vacancies.length}</Badge>
        </div>
        <div className="vacancy-grid mt-2">
          {data.vacancies.map((vacancy) => (
            <div className="vacancy-card" key={vacancy.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <div className="inline"><Badge tone="neutral">{vacancy.league_name}</Badge>{vacancy.international && <Badge tone="blue">Internacional</Badge>}</div>
                <b className="gold">{Math.round(vacancy.interest * 100)}%</b>
              </div>
              <h3>{vacancy.club_name}</h3>
              <p className="small muted">Entrenador: {vacancy.manager_name} · {vacancy.position}º de {vacancy.teams} · {vacancy.expectation}</p>
              <div className="vacancy-numbers">
                <div><span>Caja</span><b>{money(vacancy.budget)}</b></div>
                <div><span>Salarios</span><b>{money(vacancy.wage_budget)}</b></div>
                <div><span>Junta</span><b>{vacancy.board_confidence}/100</b></div>
                <div><span>Nivel</span><b>{vacancy.standard}</b></div>
              </div>
              <Button
                size="sm"
                variant={vacancy.application_status === 'offer' ? 'ghost' : 'primary'}
                icon={Send}
                onClick={() => apply(vacancy)}
                loading={busy === vacancy.id}
                disabled={vacancy.application_status === 'offer'}
                data-testid={`vacancy-apply-${vacancy.id}`}
              >
                {vacancy.application_status === 'offer' ? 'Oferta abierta' : 'Presentar candidatura'}
              </Button>
            </div>
          ))}
          {!data.vacancies.length && <p className="small muted">No hay vacantes ahora mismo. Actualiza el mercado más adelante.</p>}
        </div>
      </Card>

      {result && <Card className="mt-2"><Badge tone={resultAccepted ? 'ok' : 'neutral'} className="vacancy-applied">{result}</Badge>{resultAccepted && <Button size="sm" className="mt-2" onClick={() => navigate('/game/jobs')}>Ir a Trabajo y seguridad</Button>}</Card>}

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">MERCADO DE ENTRENADORES</div><h3 style={{ margin: '3px 0 0' }}>Últimos cambios de entrenador</h3></div>
          <Badge tone="neutral">{data.changes.length}</Badge>
        </div>
        <div className="stack-sm mt-2">
          {data.changes.map((change, index) => (
            <div className="manager-change-row" key={`${change.date}-${change.club_id}-${index}`}>
              <Badge tone={change.type === 'sack' ? 'danger' : 'ok'}>{change.type === 'sack' ? 'Destituido' : 'Nuevo'}</Badge>
              <div><b>{change.club_name}</b><span>{change.league_name} · {dateLabel(change.date)} · {change.old_manager} → {change.new_manager}</span><span>{change.reason}</span></div>
            </div>
          ))}
          {!data.changes.length && <p className="small muted">Todavía no ha habido cambios de entrenador en esta partida.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <h3>Candidaturas</h3>
        <div className="stack-sm mt-2">
          {data.applications.map((application, index) => (
            <div className="vacancy-application" key={`${application.date}-${application.vacancy_id}-${index}`}>
              <Badge tone={application.status === 'offer' ? 'ok' : 'danger'}>{application.status === 'offer' ? 'Oferta' : 'Rechazada'}</Badge>
              <div><b>{application.club_name}</b><span>{application.league_name} · {dateLabel(application.date)} · {application.message}</span></div>
              <b className="small">{Math.round(application.chance * 100)}%</b>
              {application.status === 'offer' && <Button size="sm" variant="ghost" onClick={() => navigate('/game/jobs')}>Ver oferta</Button>}
            </div>
          ))}
          {!data.applications.length && <p className="small muted">Todavía no has presentado ninguna candidatura.</p>}
        </div>
      </Card>
    </>
  )
}
