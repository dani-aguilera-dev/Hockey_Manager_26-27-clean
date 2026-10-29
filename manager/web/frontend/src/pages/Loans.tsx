import { useEffect, useState } from 'react'
import { ArrowLeftRight, CheckCircle2, Repeat, Users, XCircle } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { LoanOutgoing, LoanTarget, LoansData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, StatCard } from '../components/ui'

type InSelection = { wage: number; time: string }
type OutSelection = { club: string; wage: number; time: string }

export default function LoansPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<LoansData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [inSelections, setInSelections] = useState<Record<string, InSelection>>({})
  const [outSelections, setOutSelections] = useState<Record<string, OutSelection>>({})

  function load() {
    setLoading(true)
    api.get<LoansData>('/loans')
      .then(({ data }) => {
        setData(data)
        setInSelections(Object.fromEntries(data.targets.map((target) => [target.id, { wage: 50, time: 'rotacion' }])))
        setOutSelections(Object.fromEntries(data.outgoing.map((player) => [player.id, {
          club: player.interested_clubs[0]?.id || '',
          wage: 50,
          time: 'rotacion',
        }])))
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar las cesiones.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function requestLoanIn(target: LoanTarget) {
    const selection = inSelections[target.id] || { wage: 50, time: 'rotacion' }
    setBusy(`in-${target.id}`)
    try {
      const response = await api.post<{ loans: LoansData; state: unknown }>('/loans/in', {
        player_id: target.id,
        wage_share: selection.wage,
        playing_time: selection.time,
      })
      setData(response.data.loans)
      applyState(response.data.state as never)
      toast(response.message || 'Cesión solicitada.', response.data.loans.active.length ? 'success' : 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo cerrar la cesión.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function offerLoanOut(player: LoanOutgoing) {
    const selection = outSelections[player.id]
    if (!selection?.club) return
    setBusy(`out-${player.id}`)
    try {
      const response = await api.post<{ loans: LoansData; state: unknown }>('/loans/out', {
        player_id: player.id,
        club_id: selection.club,
        wage_share: selection.wage,
        playing_time: selection.time,
      })
      setData(response.data.loans)
      applyState(response.data.state as never)
      toast(response.message || 'Cesión ofrecida.', response.data.loans.active.length ? 'success' : 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo ofrecer la cesión.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Consultando el mercado de cesiones…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar las cesiones.</p></Card>

  const incoming = data.active.filter((loan) => loan.is_incoming)
  const outgoing = data.active.filter((loan) => !loan.is_incoming)

  return (
    <>
      <PageHeader
        eyebrow={`Mercado de cesiones · ${data.window_text}`}
        title="Cesiones y préstamos"
        subtitle="Refuerza la plantilla sin comprar, da minutos a tus jóvenes y controla la contribución salarial y la promesa de minutos."
        actions={<Badge tone={data.window === 'cerrado' ? 'danger' : 'ok'}>{data.window_text}</Badge>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Cesiones activas" value={data.active.length} hint={`${incoming.length} entrantes · ${outgoing.length} salientes`} tone="blue" icon={Repeat} />
        <StatCard label="Plantilla" value={`${data.squad_size} jugadores`} hint="Máximo 25 fichas senior" icon={Users} />
        <StatCard label="Objetivos cedibles" value={data.targets.length} hint="Jugadores disponibles en otros clubes" tone="gold" icon={ArrowLeftRight} />
        <StatCard label="Historial" value={data.history.length} hint="Operaciones y devoluciones" />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">CESIONES ACTIVAS</div><h3 style={{ margin: '3px 0 0' }}>Jugadores fuera de su club de origen</h3></div>
          <Badge tone="blue">{data.active.length}</Badge>
        </div>
        <div className="stack-sm mt-2">
          {data.active.map((loan) => (
            <div className="loan-active-row" key={loan.id}>
              <span className={`loan-direction ${loan.is_incoming ? 'in' : 'out'}`}>{loan.is_incoming ? 'Entra' : 'Sale'}</span>
              <div><b>{loan.player_name}</b><span>{loan.parent_club_name} → {loan.loan_club_name} · hasta {dateLabel(loan.end_date)}</span></div>
              <div className="loan-terms"><span>{loan.wage_share}% salario</span><span>{loan.playing_time_label}</span><b>{money(loan.fee)}</b></div>
            </div>
          ))}
          {!data.active.length && <p className="small muted">No hay cesiones activas. Pide una cesión o ofrece un jugador propio.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">CESIONES ENTRANTES</div><h3 style={{ margin: '3px 0 0' }}>Refuerzos disponibles</h3></div>
          <Badge tone="gold">{data.targets.length}</Badge>
        </div>
        <p className="small muted mt-1">Jugadores que no son titulares indiscutibles en su club. La contribución salarial y la promesa de minutos mejoran la aceptación.</p>
        <div className="loan-grid mt-2">
          {data.targets.slice(0, 12).map((target) => {
            const selection = inSelections[target.id] || { wage: 50, time: 'rotacion' }
            return (
              <div className="loan-card" key={target.id}>
                <div className="inline" style={{ justifyContent: 'space-between' }}>
                  <Badge tone="neutral">{target.league_name}</Badge>
                  <b className="gold">{target.overall}</b>
                </div>
                <h3>{target.name}</h3>
                <p className="small muted">{target.team_name} · {target.subposition} · {target.age} años</p>
                <div className="loan-card-numbers"><span>Tasa {money(target.loan_fee)}</span><span>Valor {money(target.value)}</span></div>
                <div className="loan-selects">
                  <label className="field"><span>Salario</span><select value={selection.wage} onChange={(event) => setInSelections({ ...inSelections, [target.id]: { ...selection, wage: Number(event.target.value) } })}>{target.wage_share_options.map((value) => <option key={value} value={value}>{value}%</option>)}</select></label>
                  <label className="field"><span>Minutos</span><select value={selection.time} onChange={(event) => setInSelections({ ...inSelections, [target.id]: { ...selection, time: event.target.value } })}>{target.playing_time_options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>
                </div>
                <Button size="sm" variant="primary" icon={ArrowLeftRight} onClick={() => requestLoanIn(target)} loading={busy === `in-${target.id}`} data-testid={`loan-in-${target.id}`}>Solicitar cesión</Button>
              </div>
            )
          })}
          {!data.targets.length && <p className="small muted">No hay jugadores disponibles para cesión en este momento.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">CESIONES SALIENTES</div><h3 style={{ margin: '3px 0 0' }}>Da minutos a tu plantilla</h3></div>
          <Badge tone="neutral">{data.outgoing.length}</Badge>
        </div>
        <p className="small muted mt-1">Ofrece un jugador a un club interesado. Los clubes con nivel deportivo acorde al jugador tienen más probabilidades de aceptar.</p>
        <div className="loan-grid mt-2">
          {data.outgoing.slice(0, 10).map((player) => {
            const selection = outSelections[player.id]
            if (!selection) return null
            return (
              <div className="loan-card" key={player.id}>
                <div className="inline" style={{ justifyContent: 'space-between' }}>
                  <Badge tone={player.is_key ? 'gold' : 'neutral'}>{player.is_key ? 'Importante' : 'Cedible'}</Badge>
                  <b className="gold">{player.overall}</b>
                </div>
                <h3>{player.name}</h3>
                <p className="small muted">{player.subposition} · {player.age} años · tasa {money(player.loan_fee)}</p>
                <div className="loan-selects">
                  <label className="field"><span>Club</span><select value={selection.club} onChange={(event) => setOutSelections({ ...outSelections, [player.id]: { ...selection, club: event.target.value } })}>{player.interested_clubs.map((club) => <option key={club.id} value={club.id}>{club.name} · {club.league_name}</option>)}</select></label>
                  <label className="field"><span>Salario</span><select value={selection.wage} onChange={(event) => setOutSelections({ ...outSelections, [player.id]: { ...selection, wage: Number(event.target.value) } })}>{player.wage_share_options.map((value) => <option key={value} value={value}>{value}%</option>)}</select></label>
                  <label className="field"><span>Minutos</span><select value={selection.time} onChange={(event) => setOutSelections({ ...outSelections, [player.id]: { ...selection, time: event.target.value } })}>{player.playing_time_options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>
                </div>
                <Button size="sm" variant="primary" icon={Repeat} onClick={() => offerLoanOut(player)} loading={busy === `out-${player.id}`} data-testid={`loan-out-${player.id}`}>Ofrecer cesión</Button>
              </div>
            )
          })}
          {!data.outgoing.length && <p className="small muted">No hay jugadores cedibles con clubes interesados.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <h3>Historial de cesiones</h3>
        <div className="stack-sm mt-2">
          {data.history.map((entry, index) => (
            <div className="loan-history-row" key={`${entry.date}-${entry.player_id}-${index}`}>
              <Badge tone={entry.accepted ? 'ok' : 'danger'}>{entry.returned_on ? 'Devuelto' : entry.accepted ? 'Cerrada' : 'Rechazada'}</Badge>
              <div><b>{entry.player_name}</b><span>{entry.parent_club_name} → {entry.loan_club_name} · {entry.message}</span></div>
              <span className="small muted">{dateLabel(entry.returned_on || entry.date)}</span>
            </div>
          ))}
          {!data.history.length && <p className="small muted">Todavía no hay operaciones de cesión.</p>}
        </div>
      </Card>
    </>
  )
}
