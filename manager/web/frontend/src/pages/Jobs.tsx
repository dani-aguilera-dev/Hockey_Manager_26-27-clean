import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, Check, Handshake, LogOut, RefreshCw, ShieldAlert, X } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { JobOffer, JobsData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../lib/i18n'
import { Badge, Button, Card, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

const statusTones: Record<string, 'ok' | 'gold' | 'danger' | 'neutral'> = {
  estable: 'ok',
  observacion: 'gold',
  peligro: 'danger',
  ultimatum: 'danger',
}

export default function JobsPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [data, setData] = useState<JobsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [accepted, setAccepted] = useState<string | null>(null)

  function load() {
    setLoading(true)
    api.get<JobsData>('/jobs')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : t('No se pudo cargar la situación laboral.'), 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function generate() {
    setBusy('generate')
    try {
      const response = await api.post<{ jobs: JobsData; state: unknown }>('/jobs/offers', { force: true })
      setData(response.data.jobs)
      applyState(response.data.state as never)
      toast(response.message || t('Ofertas actualizadas.'), 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudieron buscar ofertas.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function resign() {
    if (!window.confirm(t('¿Seguro que quieres dimitir? Quedarás sin club hasta aceptar otra oferta.'))) return
    setBusy('resign')
    try {
      const response = await api.post<{ jobs: JobsData; state: unknown }>('/jobs/resign')
      applyState(response.data.state as never)
      toast(response.message || t('Has presentado la dimisión.'), 'info')
      navigate('/game')
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo presentar la dimisión.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function accept(offer: JobOffer) {
    setBusy(`accept-${offer.id}`)
    try {
      const response = await api.post<{ result: { new_club: string; pending?: boolean; pending_job?: { effective_season?: string } }; jobs: JobsData; state: unknown }>(`/jobs/offers/${offer.id}/accept`)
      setData(response.data.jobs)
      applyState(response.data.state as never)
      if (!response.data.result.pending) {
        setAccepted(response.data.result.new_club)
      }
      toast(response.message || t('Oferta aceptada.'), 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo aceptar la oferta.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function reject(offer: JobOffer) {
    setBusy(`reject-${offer.id}`)
    try {
      const response = await api.post<{ jobs: JobsData; state: unknown }>(`/jobs/offers/${offer.id}/reject`)
      setData(response.data.jobs)
      applyState(response.data.state as never)
      toast(response.message || t('Oferta rechazada.'), 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo rechazar la oferta.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label={t('Revisando el mercado de entrenadores…')} />
  if (!data) return <Card><p className="muted">{t('No se pudo cargar la situación laboral.')}</p></Card>

  const { club, security, contract } = data
  return (
    <>
      <PageHeader
        eyebrow={`${club.league_name} · ${club.position}º de ${club.teams}`}
        title={t('Trabajo y seguridad')}
        subtitle={t('Confianza de la junta, contrato y ofertas de tu liga u otras ligas. Las ofertas de la misma liga cambian de club de inmediato; las de otra liga se firman para la próxima temporada.')}
        actions={<><Badge tone={statusTones[security.status] || 'neutral'}>{t(security.status_label)}</Badge><Button icon={RefreshCw} onClick={load}>{t('Actualizar')}</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label={t('Confianza de la junta')} value={`${club.board_confidence}/100`} hint={t('Presión {pressure} · paciencia {patience}/5', { pressure: club.board_pressure, patience: club.board_patience })} tone={club.board_confidence >= 60 ? 'ok' : club.board_confidence >= 40 ? 'gold' : 'danger'} icon={ShieldAlert} />
        <StatCard label={t('Afición')} value={`${club.fan_confidence}/100`} hint={t('Apoyo de la grada')} tone="blue" />
        <StatCard label={t('Valoración')} value={`${club.manager_rating}/100`} hint={security.form === '—' ? t('Sin partidos') : t('Forma {value}', { value: security.form })} tone="gold" icon={Briefcase} />
        <StatCard label={t('Riesgo')} value={`${security.risk}%`} hint={t('{points} puntos en los últimos 5', { points: security.form_points })} tone={security.risk >= 60 ? 'danger' : 'ok'} />
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">{t('SEGURIDAD')}</div><h3 style={{ margin: '3px 0 0' }}>{club.name}</h3></div>
            <Badge tone={statusTones[security.status] || 'neutral'}>{t(security.status_label)}</Badge>
          </div>
          <div className="job-security mt-2">
            <div><span>{t('Objetivo')}</span><b>{t(club.board_expectation || 'Consolidar el proyecto')}</b></div>
            <div><span>{t('Posición')}</span><b>{club.position}º de {club.teams}</b></div>
            <div><span>{t('Forma')}</span><b>{security.form}</b></div>
            <div><span>{t('Caja')}</span><b>{money(club.budget)}</b></div>
            <div><span>{t('Masa salarial')}</span><b>{money(club.wage_budget)}</b></div>
          </div>
          <div className="mt-2"><Progress value={club.board_confidence} tone={club.board_confidence >= 60 ? 'ok' : club.board_confidence >= 40 ? 'gold' : 'danger'} /></div>
          <p className="small muted mt-1">{t('La confianza baja si los resultados y la posición quedan por debajo del objetivo. En tu club, un ultimátum no expulsa automáticamente: la junta sigue evaluando. Los clubes IA sí pueden cambiar de entrenador.')}</p>
        </Card>

        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">{t('CONTRATO')}</div><h3 style={{ margin: '3px 0 0' }}>{t('Tu situación')}</h3></div>
            <Handshake size={20} className="gold" />
          </div>
          {data.user_sacked && <Badge tone="danger" className="job-sacked">{t('Sin club · busca un banquillo')}</Badge>}
          <div className="job-security mt-2">
            <div><span>{t('Club')}</span><b>{contract.club_name}</b></div>
            <div><span>{t('Salario')}</span><b>{money(contract.salary)}</b></div>
            <div><span>{t('Años')}</span><b>{contract.years}</b></div>
            <div><span>{t('Inicio')}</span><b>{contract.started}</b></div>
            <div><span>{t('Hasta')}</span><b>{contract.until}</b></div>
          </div>
          {accepted && <Badge tone="ok" className="job-accepted">{t('Nuevo club: {club}', { club: accepted })}</Badge>}
          {data.pending_job?.club_name && <Badge tone="gold" className="job-pending">{t('Acuerdo: {club} · {season}', { club: data.pending_job.club_name, season: data.pending_job.effective_season || '' })}</Badge>}
          {!data.user_sacked && (
            <div className="actions mt-2">
              <Button size="sm" variant="ghost" icon={LogOut} onClick={resign} loading={busy === 'resign'} data-testid="jobs-resign">{t('Dimisión')}</Button>
            </div>
          )}
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">{t('OFERTAS')}</div><h3 style={{ margin: '3px 0 0' }}>{t('Banquillos disponibles')}</h3></div>
          <div className="actions"><Badge tone="gold">{data.offers.length}</Badge><Button size="sm" variant="primary" icon={Briefcase} onClick={generate} loading={busy === 'generate'} data-testid="jobs-generate">{t('Buscar ofertas')}</Button></div>
        </div>
        <div className="job-offer-grid mt-2">
          {data.offers.map((offer) => (
            <div className="job-offer-card" key={offer.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><div className="inline"><Badge tone="neutral">{offer.league_name}</Badge>{offer.cross_league && <Badge tone="gold">{t('Otra liga · próxima temporada')}</Badge>}{offer.international && <Badge tone="blue">{t('Internacional')}</Badge>}</div><span className="small muted">{offer.position}º</span></div>
              <h3>{offer.club_name}</h3>
              <p className="small muted">{offer.project}</p>
              <div className="job-offer-numbers">
                <div><span>{t('Salario')}</span><b>{money(offer.salary)}</b></div>
                <div><span>{t('Años')}</span><b>{offer.years}</b></div>
                <div><span>{t('Caja')}</span><b>{money(offer.budget)}</b></div>
                <div><span>{t('Salarios')}</span><b>{money(offer.wage_budget)}</b></div>
              </div>
              <p className="small muted">{t('Objetivo: {expectation} · expira {date}', { expectation: offer.expectation, date: dateLabel(offer.expires) })}</p>
              <div className="actions">
                <Button size="sm" variant="primary" icon={Check} onClick={() => accept(offer)} loading={busy === `accept-${offer.id}`} data-testid={`job-accept-${offer.id}`}>{offer.cross_league ? t('Firmar próxima temporada') : t('Aceptar')}</Button>
                <Button size="sm" variant="ghost" icon={X} onClick={() => reject(offer)} loading={busy === `reject-${offer.id}`} data-testid={`job-reject-${offer.id}`}>{t('Rechazar')}</Button>
              </div>
            </div>
          ))}
          {!data.offers.length && <p className="small muted">{t('No hay ofertas abiertas. Pulsa “Buscar ofertas” para que los clubes de tu liga y de otras ligas se pronuncien.')}</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <h3>{t('Historial de ofertas')}</h3>
        <div className="stack-sm mt-2">
          {data.history.map((entry, index) => (
            <div className="job-history-row" key={`${entry.date}-${entry.offer_id}-${index}`}>
              <Badge tone={entry.type === 'accepted' ? 'ok' : entry.type === 'accepted_pending' ? 'gold' : 'neutral'}>{entry.type === 'accepted' ? t('Aceptada') : entry.type === 'accepted_pending' ? t('Acuerdo') : t('Rechazada')}</Badge>
              <div><b>{entry.from_club} → {entry.to_club}</b><span>{dateLabel(entry.date)} · {entry.message}</span></div>
              <b>{money(entry.salary)}</b>
            </div>
          ))}
          {!data.history.length && <p className="small muted">{t('Todavía no has aceptado ni rechazado ninguna oferta.')}</p>}
        </div>
      </Card>
    </>
  )
}
