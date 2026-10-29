import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, BadgeEuro, Send } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { Negotiation, PlayerDetailPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, Crest, Field, LoadingBlock, PageHeader } from '../components/ui'

export default function MarketPlayerPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { game, applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<PlayerDetailPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [fee, setFee] = useState('')
  const [salary, setSalary] = useState('')
  const [years, setYears] = useState('3')
  const [sending, setSending] = useState(false)
  const [negotiation, setNegotiation] = useState<Negotiation | null>(null)

  useEffect(() => {
    if (!id) return
    api.get<PlayerDetailPayload>(`/player/${id}`)
      .then(({ data }) => {
        setData(data)
        setFee(String(data.market?.asking || 0))
        setSalary(String(data.market?.minimum_salary || data.player.salary || 0))
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el jugador.', 'danger'))
      .finally(() => setLoading(false))
  }, [id, toast])

  function useCounter(next: Negotiation) {
    setNegotiation(next)
    if (next.counter) {
      setFee(String(next.counter.fee))
      setSalary(String(next.counter.salary))
      setYears(String(next.counter.years))
    }
  }

  async function offer() {
    if (!id || !data?.market) return
    setSending(true)
    try {
      const response = await api.post<{ state?: unknown; negotiation?: Negotiation }>(`/market/negotiate/${id}`, {
        fee: Number(fee),
        salary: Number(salary),
        years: Number(years),
      })
      if (response.data.state) applyState(response.data.state as never)
      const next = response.data.negotiation
      if (next && (next.status === 'accepted' || next.status === 'pending_window')) {
        toast(response.message || 'Acuerdo cerrado.', 'success')
        navigate('/game/market')
        return
      }
      if (next) {
        useCounter(next)
        toast(response.message || 'Hay una contraoferta sobre la mesa.', 'warning')
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : 'La oferta fue rechazada.', 'danger')
    } finally {
      setSending(false)
    }
  }

  async function respond(action: 'accept' | 'counter' | 'walk') {
    if (!negotiation) return
    setSending(true)
    try {
      const response = await api.post<{ state?: unknown; negotiation?: Negotiation }>(`/market/negotiations/${negotiation.id}`, {
        action,
        fee: Number(fee),
        salary: Number(salary),
        years: Number(years),
      })
      if (response.data.state) applyState(response.data.state as never)
      const next = response.data.negotiation
      if (next) {
        setNegotiation(next)
        if (next.status === 'accepted' || next.status === 'pending_window') {
          toast(response.message || 'Negociación cerrada.', 'success')
          navigate('/game/market')
          return
        }
        if (next.counter && action === 'counter') useCounter(next)
      }
      toast(response.message || 'Negociación actualizada.', action === 'walk' ? 'info' : 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo continuar la negociación.', 'danger')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <LoadingBlock label="Cargando negociación…" />
  if (!data) return <Card><p className="muted">No se encontró el jugador.</p></Card>

  const { player, owner, market } = data
  const closed = !market || market.window === 'cerrado'

  return (
    <>
      <PageHeader
        eyebrow={`Mercado · ${market?.window_text || 'Consulta'}`}
        title="Negociación"
        subtitle={`${player.name} · ${player.subposition} · ${player.origin_team ? `procede de ${player.origin_team}` : data.owner_name}`}
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game/market')}>Volver al mercado</Button>}
      />

      <div className="market-player-hero">
        <Avatar player={player} size={92} />
        <div style={{ flex: 1 }}>
          <div className="inline">
            <Badge tone="gold">{player.overall.toFixed(1)} OVR</Badge>
            <Badge tone="blue">{player.stars}</Badge>
            {player.available ? <Badge tone="ok">Disponible</Badge> : <Badge tone="danger">{player.absence_label}</Badge>}
          </div>
          <h1>{player.name}</h1>
          <p>{player.age} años · {player.archetype} · {player.origin_team ? `procede de ${player.origin_team}` : data.owner_name} · {player.apps} PJ · {player.season_goals} G · {player.season_assists} A</p>
        </div>
        {owner && <Crest src={owner.crest} name={owner.name} size={62} />}
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">LECTURA DE LA OPERACIÓN</div><h3 style={{ margin: '3px 0 0' }}>Contexto antes de negociar</h3></div><Badge tone={game && Number(fee) <= game.team.transfer_budget ? 'ok' : 'warn'}>{game && Number(fee) <= game.team.transfer_budget ? 'Dentro de presupuesto' : 'Revisa el presupuesto'}</Badge></div>
        <div className="news-detail-stats mt-2">
          <div><span>Edad</span><b>{player.age} años</b></div>
          <div><span>Liga</span><b>{player.league_label}</b></div>
          <div><span>Rendimiento</span><b>{player.rating.toFixed(2)} · {player.apps} PJ</b></div>
          <div><span>Goles / asistencias</span><b>{player.season_goals} / {player.season_assists}</b></div>
          <div><span>Contrato</span><b>{player.contract_until}</b></div>
          <div><span>Presupuesto fichajes</span><b>{money(game?.team.transfer_budget || 0)}</b></div>
        </div>
        <p className="small muted mt-2">{player.age <= 23 ? 'Jugador joven: el valor puede crecer, pero necesita minutos y adaptación.' : player.age >= 30 ? 'Jugador veterano: aporta experiencia inmediata, pero exige contrato y gestión de carga.' : 'Jugador en plenitud: el coste de mercado suele ser alto y la competencia por su firma también.'} {player.rating >= 7 ? 'Su rendimiento reciente invita a competir por él.' : 'Su rendimiento aún no justifica una prima excesiva.'}</p>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>Negociación de traspaso</h3>
            {negotiation && <Badge tone={negotiation.status === 'accepted' || negotiation.status === 'pending_window' ? 'ok' : 'warn'}>{negotiation.status === 'open' ? `Ronda ${negotiation.round}/${negotiation.max_rounds}` : negotiation.status === 'accepted' ? 'Acuerdo' : negotiation.status === 'pending_window' ? 'Pendiente de ventana' : negotiation.status}</Badge>}
          </div>

          {negotiation ? (
            <div className="stack-sm mt-2">
              <div className="notice notice-warn">
                <b>{negotiation.club_name}</b>
                <p style={{ margin: '4px 0 0' }}>{negotiation.message}</p>
              </div>
              <div className="news-detail-stats">
                <div><span>Piden por traspaso</span><b>{money(negotiation.ask.fee)}</b></div>
                <div><span>Salario pedido</span><b>{money(negotiation.ask.salary)}</b></div>
                <div><span>Tu oferta</span><b>{money(negotiation.offer.fee)} + {money(negotiation.offer.salary)}</b></div>
                <div><span>Duración</span><b>{negotiation.offer.years} años</b></div>
              </div>
              {negotiation.status === 'open' && (
                <>
                  <div className="form-grid">
                    <Field label="Traspaso (€)"><input value={fee} onChange={(event) => setFee(event.target.value.replace(/\D/g, ''))} inputMode="numeric" /></Field>
                    <Field label="Salario anual (€)"><input value={salary} onChange={(event) => setSalary(event.target.value.replace(/\D/g, ''))} inputMode="numeric" /></Field>
                    <Field label="Duración"><select value={years} onChange={(event) => setYears(event.target.value)}><option value="1">1 año</option><option value="2">2 años</option><option value="3">3 años</option><option value="4">4 años</option><option value="5">5 años</option></select></Field>
                  </div>
                  <div className="actions">
                    <Button variant="primary" size="sm" onClick={() => respond('accept')} loading={sending}>Aceptar contraoferta</Button>
                    <Button size="sm" onClick={() => respond('counter')} loading={sending}>Enviar contraoferta</Button>
                    <Button size="sm" variant="ghost" onClick={() => respond('walk')} loading={sending}>Retirarse</Button>
                  </div>
                </>
              )}
              {(negotiation.status === 'accepted' || negotiation.status === 'pending_window') && (
                <Button variant="primary" onClick={() => navigate('/game/market')}>Volver al mercado</Button>
              )}
            </div>
          ) : closed ? (
            <div className="notice notice-warn mt-2">El mercado está cerrado. Podrás abrir la negociación en la próxima ventana.</div>
          ) : (
            <div className="form-stack mt-2">
              <Field label="Traspaso (€)" hint={market ? `Precio de salida ${money(market.asking)}` : undefined}><input value={fee} onChange={(event) => setFee(event.target.value.replace(/\D/g, ''))} inputMode="numeric" /></Field>
              <Field label="Salario anual (€)" hint={market ? `Mínimo ${money(market.minimum_salary)}` : undefined}><input value={salary} onChange={(event) => setSalary(event.target.value.replace(/\D/g, ''))} inputMode="numeric" /></Field>
              <Field label="Duración (años)"><select value={years} onChange={(event) => setYears(event.target.value)}><option value="1">1 año</option><option value="2">2 años</option><option value="3">3 años</option><option value="4">4 años</option><option value="5">5 años</option></select></Field>
              <Button variant="primary" size="lg" icon={Send} onClick={offer} loading={sending} disabled={!game}>Abrir negociación</Button>
              <p className="small muted">El club vendedor y el jugador pueden aceptar, rechazar o contraofertar. El ojeador estima el nivel: {market?.scout || '—'}.</p>
            </div>
          )}
        </Card>
        <Card>
          <h3>Ficha rápida</h3>
          <div className="stack-sm">
            <div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Precio de salida</span><b>{market ? money(market.asking) : '—'}</b></div>
            <div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Salario actual</span><b>{money(player.salary)}</b></div>
            <div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Contrato</span><b>{player.contract_until}</b></div>
            <div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Potencial</span><b>{player.potential.toFixed(1)}</b></div>
            <div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Valor de mercado</span><b>{money(player.value)}</b></div>
          </div>
          <div className="notice notice-info mt-2"><BadgeEuro size={16} /><div>La negociación consume presupuesto de fichajes. Revisa tu caja antes de enviar.</div></div>
        </Card>
      </div>
    </>
  )
}
