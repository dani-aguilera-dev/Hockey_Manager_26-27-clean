import { useEffect, useState } from 'react'
import { GraduationCap, Handshake, Network, ShieldCheck, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { AffiliateCandidate, AffiliateOverview, AffiliatesPayload, MentoringOverview, MentoringPair } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

export default function AffiliatesPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<AffiliatesPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [mentorId, setMentorId] = useState('')
  const [menteeId, setMenteeId] = useState('')
  const [focus, setFocus] = useState('tecnica')

  function load() {
    setLoading(true)
    api.get<AffiliatesPayload>('/affiliates')
      .then(({ data }) => {
        setData(data)
        setMentorId((current) => current || data.mentoring.mentors[0]?.id || '')
        setMenteeId((current) => current || data.mentoring.mentees[0]?.id || '')
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar los afiliados.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function requestAffiliate(candidate: AffiliateCandidate) {
    setBusy(`affiliate-${candidate.id}`)
    try {
      const response = await api.post<{ affiliates: AffiliateOverview; mentoring: MentoringOverview; state: unknown }>('/affiliates/request', { club_id: candidate.id })
      setData({ affiliates: response.data.affiliates, mentoring: response.data.mentoring })
      applyState(response.data.state as never)
      toast(response.message || 'Afiliación solicitada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo firmar la afiliación.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function endAffiliate(affiliateId: string) {
    setBusy(`end-${affiliateId}`)
    try {
      const response = await api.post<{ affiliates: AffiliateOverview; mentoring: MentoringOverview; state: unknown }>(`/affiliates/${affiliateId}/end`)
      setData({ affiliates: response.data.affiliates, mentoring: response.data.mentoring })
      applyState(response.data.state as never)
      toast(response.message || 'Afiliación finalizada.', 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo finalizar la afiliación.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function assignMentoring() {
    if (!mentorId || !menteeId) return
    setBusy('mentoring')
    try {
      const response = await api.post<{ affiliates: AffiliateOverview; mentoring: MentoringOverview; state: unknown }>('/mentoring', {
        mentor_id: mentorId,
        mentee_id: menteeId,
        focus,
      })
      setData({ affiliates: response.data.affiliates, mentoring: response.data.mentoring })
      applyState(response.data.state as never)
      toast(response.message || 'Plan de mentoría creado.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo crear el plan de mentoría.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function endMentoring(pair: MentoringPair) {
    setBusy(`mentoring-${pair.id}`)
    try {
      const response = await api.delete<{ affiliates: AffiliateOverview; mentoring: MentoringOverview; state: unknown }>(`/mentoring/${pair.id}`)
      setData({ affiliates: response.data.affiliates, mentoring: response.data.mentoring })
      applyState(response.data.state as never)
      toast(response.message || 'Plan finalizado.', 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo finalizar el plan.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Revisando la red de clubes y la cantera…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar los afiliados.</p></Card>

  const affiliates = data.affiliates
  const mentoring = data.mentoring

  return (
    <>
      <PageHeader
        eyebrow="Cantera · red de clubes · desarrollo"
        title="Afiliados y mentoring"
        subtitle="Construye una red de clubes filiales, mejora el ojeo y la cantera, y empareja a tus veteranos con los jóvenes de mayor proyección."
        actions={<Badge tone="blue">{affiliates.affiliates.length} afiliados · {mentoring.pairs.length} mentorías</Badge>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Clubes afiliados" value={affiliates.affiliates.length} hint="Red de desarrollo" tone="blue" icon={Network} />
        <StatCard label="Ojeo" value={affiliates.scouting} hint="Beneficio de afiliados" tone="gold" icon={ShieldCheck} />
        <StatCard label="Cantera" value={affiliates.youth} hint={`Academia ${affiliates.academy_rating}`} icon={GraduationCap} />
        <StatCard label="Mentorías activas" value={mentoring.pairs.length} hint={`${mentoring.mentors.length} mentores · ${mentoring.mentees.length} jóvenes`} icon={Users} />
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">CLUBES AFILIADOS</div><h3 style={{ margin: '3px 0 0' }}>Red actual</h3></div>
            <Handshake size={22} className="gold" />
          </div>
          <div className="stack-sm mt-2">
            {affiliates.affiliates.map((affiliate) => (
              <div className="affiliate-row" key={affiliate.id}>
                <span className="sponsor-mark"><Network size={17} /></span>
                <div><b>{affiliate.club_name}</b><span>{affiliate.league_name} · {affiliate.city} · desde {dateLabel(affiliate.since)}</span><span className="gold small">{affiliate.benefits.join(' · ')}</span></div>
                <div className="affiliate-actions"><b>{money(affiliate.annual_fee)}</b><Button size="sm" variant="ghost" onClick={() => endAffiliate(affiliate.id)} loading={busy === `end-${affiliate.id}`}>Finalizar</Button></div>
              </div>
            ))}
            {!affiliates.affiliates.length && <p className="small muted">Todavía no hay clubes afiliados. Firma una afiliación para ampliar la red.</p>}
          </div>
        </Card>

        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">BENEFICIOS</div><h3 style={{ margin: '3px 0 0' }}>Qué aporta la red</h3></div>
            <Badge tone="gold">{affiliates.benefits.length}</Badge>
          </div>
          <div className="stack-sm mt-2">
            {affiliates.benefits.map((benefit) => <div className="affiliate-benefit" key={benefit}>{benefit}</div>)}
          </div>
          <p className="small muted mt-2">Los afiliados también aparecen como destino prioritario en las cesiones salientes.</p>
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">CANDIDATOS A AFILIACIÓN</div><h3 style={{ margin: '3px 0 0' }}>Clubes de menor nivel</h3></div>
          <Badge tone="blue">{affiliates.candidates.length}</Badge>
        </div>
        <div className="affiliate-grid mt-2">
          {affiliates.candidates.map((candidate) => (
            <div className="affiliate-card" key={candidate.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <Badge tone="neutral">{candidate.league_name}</Badge>
                <span className="small muted">{Math.round(candidate.approval_chance * 100)}%</span>
              </div>
              <h3>{candidate.name}</h3>
              <p className="small muted">{candidate.city} · {candidate.country}</p>
              <div className="affiliate-numbers"><span>Cuota {money(candidate.annual_fee)}</span><span>Academia {candidate.academy_rating}</span></div>
              <Button size="sm" variant="primary" icon={Handshake} onClick={() => requestAffiliate(candidate)} loading={busy === `affiliate-${candidate.id}`} data-testid={`affiliate-${candidate.id}`}>Firmar afiliación</Button>
            </div>
          ))}
          {!affiliates.candidates.length && <p className="small muted">No hay clubes disponibles para afiliación.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">MENTORING</div><h3 style={{ margin: '3px 0 0' }}>Veteranos y jóvenes</h3></div>
          <Badge tone="gold">{mentoring.pairs.length} activos</Badge>
        </div>
        <p className="small muted mt-1">Cada cuatro sesiones el joven mejora atributos del plan y su relación con el grupo. Los cedidos no pueden participar.</p>
        <div className="mentoring-grid mt-2">
          {mentoring.pairs.map((pair) => (
            <div className="mentoring-row" key={pair.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <Badge tone="blue">{pair.focus_label}</Badge>
                <span className="small muted">{pair.sessions} sesiones</span>
              </div>
              <b>{pair.mentor_name} → {pair.mentee_name}</b>
              <span className="small muted">{pair.mentor_overall} OVR mentor · {pair.mentee_overall} / {pair.mentee_potential} joven</span>
              <Progress value={pair.progress} tone="gold" />
              <Button size="sm" variant="ghost" onClick={() => endMentoring(pair)} loading={busy === `mentoring-${pair.id}`}>Finalizar plan</Button>
            </div>
          ))}
          {!mentoring.pairs.length && <p className="small muted">No hay mentorías activas. Crea un plan con un veterano y un joven.</p>}
        </div>
        <div className="mentoring-form mt-2">
          <Field label="Mentor">
            <select value={mentorId} onChange={(event) => setMentorId(event.target.value)}>
              {mentoring.mentors.map((mentor) => <option key={mentor.id} value={mentor.id}>{mentor.name} · {mentor.overall} OVR · {mentor.age} años</option>)}
            </select>
          </Field>
          <Field label="Joven">
            <select value={menteeId} onChange={(event) => setMenteeId(event.target.value)}>
              {mentoring.mentees.map((mentee) => <option key={mentee.id} value={mentee.id}>{mentee.name} · {mentee.overall}/{mentee.potential} · {mentee.age} años</option>)}
            </select>
          </Field>
          <Field label="Plan">
            <select value={focus} onChange={(event) => setFocus(event.target.value)}>
              {mentoring.focus_options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </Field>
          <Button variant="primary" icon={GraduationCap} onClick={assignMentoring} loading={busy === 'mentoring'} disabled={!mentorId || !menteeId} data-testid="mentoring-assign">Crear mentoría</Button>
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <h3>Historial de afiliaciones</h3>
          <div className="stack-sm mt-2">
            {affiliates.history.map((entry, index) => (
              <div className="affiliate-history-row" key={`${entry.date}-${entry.club_id}-${index}`}>
                <Badge tone={entry.ended_on ? 'neutral' : entry.accepted ? 'ok' : 'danger'}>{entry.ended_on ? 'Finalizada' : entry.accepted ? 'Firmada' : 'Rechazada'}</Badge>
                <div><b>{entry.club_name}</b><span>{entry.league_name} · {entry.message}</span></div>
                <span className="small muted">{dateLabel(entry.ended_on || entry.date)}</span>
              </div>
            ))}
            {!affiliates.history.length && <p className="small muted">Sin movimientos de afiliación.</p>}
          </div>
        </Card>
        <Card>
          <h3>Historial de mentorías</h3>
          <div className="stack-sm mt-2">
            {mentoring.history.map((pair, index) => (
              <div className="affiliate-history-row" key={`${pair.id}-${index}`}>
                <Badge tone="neutral">Finalizada</Badge>
                <div><b>{pair.mentor_name} → {pair.mentee_name}</b><span>{pair.focus_label} · {pair.sessions} sesiones</span></div>
              </div>
            ))}
            {!mentoring.history.length && <p className="small muted">Sin mentorías finalizadas.</p>}
          </div>
        </Card>
      </div>
    </>
  )
}
