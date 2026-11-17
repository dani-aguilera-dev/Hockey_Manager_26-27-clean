import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, BadgeEuro, Check, Filter, RefreshCw, Search, SlidersHorizontal, Users, X } from 'lucide-react'
import { api, queryString } from '../lib/api'
import { money } from '../lib/format'
import type { IncomingOffer, MarketPayload, MarketPlayer, MarketStaff, Player } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../lib/i18n'
import { Avatar, Badge, Button, Card, EmptyState, Field, LoadingBlock, PageHeader, Tabs } from '../components/ui'
import ScoutPanel from './ScoutPanel'

type Tab = 'scout' | 'players' | 'free' | 'staff' | 'sales' | 'offers'

export default function MarketPage() {
  const navigate = useNavigate()
  const { game, applyState } = useGame()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [data, setData] = useState<MarketPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('scout')
  const [query, setQuery] = useState('')
  const [position, setPosition] = useState('')
  const [league, setLeague] = useState('')
  const [clubId, setClubId] = useState('')
  const [minAge, setMinAge] = useState('')
  const [maxAge, setMaxAge] = useState('')
  const [minOverall, setMinOverall] = useState('')
  const [maxOverall, setMaxOverall] = useState('')
  const [maxValue, setMaxValue] = useState('')
  const [attribute, setAttribute] = useState('')
  const [minAttribute, setMinAttribute] = useState('')
  const [listedOnly, setListedOnly] = useState(false)
  const [staffRole, setStaffRole] = useState('')
  const [staffMinRating, setStaffMinRating] = useState('')
  const [staffMaxSalary, setStaffMaxSalary] = useState('')
  const [visible, setVisible] = useState(30)
  const [visibleStaff, setVisibleStaff] = useState(20)
  const [visibleSales, setVisibleSales] = useState(15)
  const [busy, setBusy] = useState<string | null>(null)
  const [salesForms, setSalesForms] = useState<Record<string, { listed: boolean; price: string }>>({})

  async function load() {
    setLoading(true)
    try {
      const response = await api.get<MarketPayload>(`/market${queryString({
        q: query,
        position,
        league,
        club_id: clubId,
        min_age: minAge,
        max_age: maxAge,
        min_overall: minOverall,
        max_overall: maxOverall,
        max_value: maxValue,
        attribute,
        min_attribute: minAttribute,
        listed: listedOnly ? '1' : '',
        staff_role: staffRole,
        staff_min_rating: staffMinRating,
        staff_max_salary: staffMaxSalary,
      })}`)
      setData(response.data)
      setVisible(30)
      setVisibleStaff(20)
      setVisibleSales(15)
      setSalesForms(Object.fromEntries(response.data.own_players.map((player) => [player.id, {
        listed: Boolean(player.transfer_listed),
        price: String(player.transfer_asking_price || player.value || 0),
      }])))
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo cargar el mercado.'), 'danger')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void load() }, [])

  function resetFilters() {
    setQuery(''); setPosition(''); setLeague(''); setClubId(''); setMinAge(''); setMaxAge('')
    setMinOverall(''); setMaxOverall(''); setMaxValue(''); setAttribute(''); setMinAttribute('')
    setListedOnly(false); setStaffRole(''); setStaffMinRating(''); setStaffMaxSalary('')
  }

  async function listPlayer(player: Player) {
    const form = salesForms[player.id]
    if (!form) return
    setBusy(`list-${player.id}`)
    try {
      const response = await api.post<{ state: unknown }>(`/market/list/${player.id}`, {
        listed: form.listed,
        asking_price: Number(form.price || 0),
      })
      applyState(response.data.state as never)
      toast(response.message || t('Jugador actualizado.'), 'success')
      await load()
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo actualizar la lista.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function hireStaff(candidate: MarketStaff) {
    setBusy(`staff-${candidate.id}`)
    try {
      const response = await api.post<{ state: unknown }>('/market/staff/hire', { candidate_id: candidate.id })
      applyState(response.data.state as never)
      toast(response.message || t('Empleado contratado.'), 'success')
      await load()
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo contratar al empleado.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function offerAction(offer: IncomingOffer, action: 'accept' | 'reject') {
    setBusy(`offer-${offer.id}`)
    try {
      const response = await api.post<{ state: unknown }>(`/market/offers/${offer.id}`, { action })
      applyState(response.data.state as never)
      toast(response.message || (action === 'accept' ? t('Oferta aceptada.') : t('Oferta rechazada.')), action === 'accept' ? 'success' : 'info')
      await load()
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo procesar la oferta.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (!game) return null
  if (loading && !data) return <LoadingBlock label={t('Cargando mercado global…')} />

  const players = data?.players || []
  const freeAgents = data?.free_agents || []
  const staff = data?.staff || []
  const ownPlayers = data?.own_players || []
  const offers = data?.offers || []
  const negotiations = (data?.negotiations || []).filter((item) => item.status === 'open')
  const pendingTransfers = data?.pending_transfers || []

  const counts = { players: players.length, free: data?.free_agent_total || 0, staff: data?.staff_total || 0, sales: ownPlayers.length, offers: offers.length }
  const tabItems = [
    { value: 'scout' as Tab, label: t('Ojeador') },
    { value: 'players' as Tab, label: t('Jugadores'), count: counts.players },
    { value: 'free' as Tab, label: t('Agentes libres'), count: counts.free },
    { value: 'staff' as Tab, label: t('Staff'), count: counts.staff },
    { value: 'sales' as Tab, label: t('Ventas'), count: counts.sales },
    { value: 'offers' as Tab, label: t('Ofertas'), count: counts.offers },
  ]
  const rows = tab === 'players' ? players : tab === 'free' ? freeAgents : []

  return (
    <>
      <PageHeader
        eyebrow={t('{status} · mercado global', { status: t(game.market.status) })}
        title={t('Mercado')}
        subtitle={t('Jugadores, agentes libres y empleados de todas las ligas. Filtra por competición, edad, atributos, valor y rendimiento.')}
        actions={<><Button icon={RefreshCw} onClick={load} loading={loading}>{t('Actualizar')}</Button><Button icon={BadgeEuro} onClick={() => navigate('/game/market/renew')}>{t('Renovar')}</Button></>}
      />

      <div className="dashboard-kpis">
        <div className="stat-card"><span className="stat-top">{t('CAJA')}</span><strong>{money(game.finance.cash)}</strong><small>{t('Disponible ahora')}</small></div>
        <div className="stat-card"><span className="stat-top">{t('FICHAJES')}</span><strong>{money(game.team.transfer_budget)}</strong><small>{t('Presupuesto de traspasos')}</small></div>
        <div className="stat-card"><span className="stat-top">{t('OFERTAS')}</span><strong>{offers.length}</strong><small>{t('Recibidas por tus jugadores')}</small></div>
        <div className="stat-card"><span className="stat-top">{t('EN VENTA')}</span><strong>{ownPlayers.filter((player) => player.transfer_listed).length}</strong><small>{t('Jugadores en el escaparate')}</small></div>
      </div>

      <Card>
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
          <Tabs<Tab>
            value={tab}
            onChange={setTab}
            tabs={tabItems}
          />
          <Badge tone={data?.window === 'cerrado' ? 'warn' : 'ok'}>{t(data?.window_text || game.market.status)}</Badge>
        </div>

        {tab !== 'scout' && tab !== 'sales' && tab !== 'offers' && (
          <div className="filters market-filters">
            <Field label={t('Buscar')}><div style={{ position: 'relative' }}><Search size={14} style={{ position: 'absolute', left: 10, top: 12, color: 'var(--muted-2)' }} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t('Jugador, club, arquetipo…')} style={{ paddingLeft: 30 }} onKeyDown={(event) => event.key === 'Enter' && load()} /></div></Field>
            <Field label={t('Liga')}><select value={league} onChange={(event) => setLeague(event.target.value)}><option value="">{t('Todas las ligas')}</option>{data?.leagues.map((item) => <option key={item.code} value={item.code}>{item.short_name} · {item.country}</option>)}</select></Field>
            {tab !== 'staff' && <Field label={t('Posición')}><select value={position} onChange={(event) => setPosition(event.target.value)}><option value="">{t('Todas')}</option>{['Portero', 'Central', 'Lateral', 'Medio', 'Delantero'].map((value) => <option key={value}>{value}</option>)}</select></Field>}
            {tab === 'staff' ? (
              <>
                <Field label={t('Rol')}><select value={staffRole} onChange={(event) => setStaffRole(event.target.value)}><option value="">{t('Todos')}</option>{Object.entries(data?.staff_roles || {}).filter(([role]) => role !== 'head_coach').map(([role, label]) => <option key={role} value={role}>{label}</option>)}</select></Field>
                <Field label={t('Rating mínimo')}><input value={staffMinRating} onChange={(event) => setStaffMinRating(event.target.value.replace(/\D/g, ''))} placeholder={t('Ej. 65')} inputMode="numeric" /></Field>
                <Field label={t('Salario máximo')}><input value={staffMaxSalary} onChange={(event) => setStaffMaxSalary(event.target.value.replace(/\D/g, ''))} placeholder={t('Sin límite')} inputMode="numeric" /></Field>
              </>
            ) : (
              <>
                <Field label={t('Edad mín.')}><input value={minAge} onChange={(event) => setMinAge(event.target.value.replace(/\D/g, ''))} placeholder="16" inputMode="numeric" /></Field>
                <Field label={t('Edad máx.')}><input value={maxAge} onChange={(event) => setMaxAge(event.target.value.replace(/\D/g, ''))} placeholder="40" inputMode="numeric" /></Field>
                <Field label={t('OVR mín.')}><input value={minOverall} onChange={(event) => setMinOverall(event.target.value.replace(/[^\d.]/g, ''))} placeholder="60" inputMode="decimal" /></Field>
                <Field label={t('OVR máx.')}><input value={maxOverall} onChange={(event) => setMaxOverall(event.target.value.replace(/[^\d.]/g, ''))} placeholder="99" inputMode="decimal" /></Field>
                <Field label={t('Valor máximo')}><input value={maxValue} onChange={(event) => setMaxValue(event.target.value.replace(/\D/g, ''))} placeholder={t('Sin límite')} inputMode="numeric" /></Field>
                <Field label={t('Atributo')}><select value={attribute} onChange={(event) => setAttribute(event.target.value)}><option value="">{t('Cualquiera')}</option>{data?.attributes.map((key) => <option key={key} value={key}>{key.replaceAll('_', ' ')}</option>)}</select></Field>
                {attribute && <Field label={t('Atributo mínimo')}><input value={minAttribute} onChange={(event) => setMinAttribute(event.target.value.replace(/\D/g, ''))} placeholder="70" inputMode="numeric" /></Field>}
                {tab === 'players' && <label className="checkline"><input type="checkbox" checked={listedOnly} onChange={(event) => setListedOnly(event.target.checked)} /> {t('Solo en venta')}</label>}
              </>
            )}
            <Button variant="primary" icon={Filter} onClick={load}>{t('Aplicar filtros')}</Button>
            <Button variant="ghost" onClick={() => { resetFilters(); setTimeout(load, 0) }}>{t('Limpiar')}</Button>
          </div>
        )}
      </Card>

      {tab === 'scout' && <ScoutPanel onUseMarket={() => setTab('players')} />}

      {tab !== 'scout' && (loading ? <LoadingBlock label={t('Buscando en todas las ligas…')} /> : (
        <>
          {(tab === 'players' || tab === 'free') && (
            <div className="market-layout mt-2">
              <Card>
                <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
                  <div><div className="cat">{tab === 'free' ? t('AGENTES LIBRES') : t('MERCADO GLOBAL')}</div><h3 style={{ margin: '3px 0 0' }}>{t('{count} jugadores', { count: rows.length })}</h3></div>
                  <Badge tone="neutral">{t('Ojeador {rating}/100', { rating: game.team.staff.find((member) => member.role === 'scout')?.rating ?? 55 })}</Badge>
                </div>
                {rows.length ? (
                  <div className="market-list">
                    {rows.slice(0, visible).map((player) => <PlayerRow key={player.id} player={player} onOpen={() => navigate(`/game/player/${player.id}`)} />)}
                  </div>
                ) : <EmptyState title={t('Sin resultados')} body={t('Ajusta los filtros o busca en otra liga.')} />}
                {rows.length > visible && <div className="actions mt-2" style={{ justifyContent: 'center' }}><Button variant="ghost" onClick={() => setVisible((value) => value + 30)}>{t('Mostrar más ({count})', { count: rows.length - visible })}</Button></div>}
              </Card>
              <aside className="market-side">
                <Card><div className="cat">{t('VENTANA')}</div><h3 style={{ margin: '4px 0' }}>{t(data?.window_text || '')}</h3><p className="small muted">{t('Todas las ligas pueden fichar entre sí. Los clubes de categorías superiores tienen más presupuesto y peso.')}</p><div className="stack-sm mt-1"><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Caja')}</span><b>{money(game.finance.cash)}</b></div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Fichajes')}</span><b>{money(game.team.transfer_budget)}</b></div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Salarios')}</span><b>{money(game.finance.annual_wage_bill)}</b></div></div></Card>
                <Card><div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>{t('Ofertas recibidas')}</h3><Badge tone={offers.length ? 'warn' : 'ok'}>{offers.length}</Badge></div>{offers.length ? offers.slice(0, 3).map((offer) => <div className="offer-card mt-1" key={offer.id}><div className="offer-card-main"><b>{offer.player_name}</b><span>{offer.from_club_name} · {money(offer.fee)}</span></div><Button size="sm" onClick={() => setTab('offers')}>{t('Ver')}</Button></div>) : <p className="small muted mt-1">{t('Sin ofertas. Pon jugadores en venta o destaca con tu rendimiento.')}</p>}</Card>
                <Card><div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>{t('Negociaciones abiertas')}</h3><Badge tone={negotiations.length ? 'warn' : 'ok'}>{negotiations.length}</Badge></div>{negotiations.length ? negotiations.slice(0, 3).map((item) => <div className="offer-card mt-1" key={item.id}><div className="offer-card-main"><b>{item.player_name}</b><span>{item.club_name} · ronda {item.round}/{item.max_rounds}</span></div><Button size="sm" onClick={() => navigate(`/game/market/player/${item.player_id}`)}>{t('Abrir')}</Button></div>) : <p className="small muted mt-1">{t('Sin negociaciones abiertas.')}</p>}</Card>
                <Card><div className="cat">{t('HISTÓRICO')}</div>{game.market.history.length ? game.market.history.slice().reverse().slice(0, 5).map((item, index) => <div className="inbox-item mt-1" key={`${item.player}-${index}`}><b>{item.player}</b><span>{item.from} → {item.to}</span><p>{money(item.fee)} · {item.season}</p></div>) : <p className="small muted mt-1">{t('Todavía no hay movimientos.')}</p>}</Card>
              </aside>
            </div>
          )}

          {tab === 'staff' && (
            <Card className="mt-2">
              <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}><div><div className="cat">{t('MERCADO DE EMPLEADOS')}</div><h3 style={{ margin: '3px 0 0' }}>{t('{count} candidatos ficticios', { count: staff.length })}</h3></div><Badge tone="blue">{t('Staff libre')}</Badge></div>
              <div className="stack-sm">
                {staff.slice(0, visibleStaff).map((candidate) => (
                  <div className="market-row" key={candidate.id}>
                    <Avatar player={{ name: candidate.name, initials: candidate.name.split(' ').map((part) => part[0]).join('').slice(0, 2) }} size={42} />
                    <div className="market-row-main"><b>{candidate.name}</b><span>{candidate.role_label} · {candidate.source} · {candidate.confidence}</span><span>Rating {candidate.rating}/100 · salario {money(candidate.salary)} · contrato {candidate.contract_until}</span></div>
                    <Button size="sm" variant="primary" icon={Users} onClick={() => hireStaff(candidate)} loading={busy === `staff-${candidate.id}`}>{t('Contratar')}</Button>
                  </div>
                ))}
                {!staff.length && <EmptyState title={t('Sin candidatos')} body={t('Prueba con otro rol o rating mínimo.')} />}
              </div>
              {staff.length > visibleStaff && <div className="actions mt-2" style={{ justifyContent: 'center' }}><Button variant="ghost" onClick={() => setVisibleStaff((value) => value + 20)}>{t('Mostrar más ({count})', { count: staff.length - visibleStaff })}</Button></div>}
            </Card>
          )}

          {tab === 'sales' && (
            <Card className="mt-2">
              <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}><div><div className="cat">{t('VENTAS Y LISTA DE TRASPASO')}</div><h3 style={{ margin: '3px 0 0' }}>{t('Decide a quién pones en el escaparate')}</h3></div><Badge tone="neutral">{t('{count} jugadores', { count: ownPlayers.length })}</Badge></div>
              <div className="stack-sm">
                {ownPlayers.slice(0, visibleSales).map((player) => {
                  const form = salesForms[player.id] || { listed: player.transfer_listed, price: String(player.transfer_asking_price || player.value || 0) }
                  return (
                    <div className="market-row" key={player.id}>
                      <Avatar player={player} size={42} />
                      <div className="market-row-main"><b>{player.name}</b><span>{player.subposition} · {player.age} años · OVR {player.overall.toFixed(1)} · {player.stars}</span><span>{player.apps} PJ · {player.season_goals} G · {player.season_assists} A · rating {player.rating.toFixed(2)}</span></div>
                      <label className="checkline"><input type="checkbox" checked={form.listed} onChange={(event) => setSalesForms({ ...salesForms, [player.id]: { ...form, listed: event.target.checked } })} /> {t('En venta')}</label>
                      <div style={{ width: 150 }}><Field label={t('Precio')}><input value={form.price} onChange={(event) => setSalesForms({ ...salesForms, [player.id]: { ...form, price: event.target.value.replace(/\D/g, '') } })} inputMode="numeric" /></Field></div>
                      <Button size="sm" variant={form.listed ? 'primary' : 'secondary'} onClick={() => listPlayer(player)} loading={busy === `list-${player.id}`}>{form.listed ? t('Guardar') : t('Poner en venta')}</Button>
                    </div>
                  )
                })}
              </div>
              {ownPlayers.length > visibleSales && <div className="actions mt-2" style={{ justifyContent: 'center' }}><Button variant="ghost" onClick={() => setVisibleSales((value) => value + 15)}>{t('Mostrar más ({count})', { count: ownPlayers.length - visibleSales })}</Button></div>}
            </Card>
          )}

          {tab === 'offers' && (
            <Card className="mt-2">
              <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}><div><div className="cat">{t('OFERTAS POR TUS JUGADORES')}</div><h3 style={{ margin: '3px 0 0' }}>{t('{count} propuestas', { count: offers.length })}</h3></div><Button size="sm" variant="ghost" onClick={() => navigate('/game/market/offers')}>{t('Vista completa')}</Button></div>
              {pendingTransfers.length > 0 && (
                <div className="notice notice-warn mb-2">
                  <Badge tone="warn">{t('Pendiente de ventana')}</Badge>
                  <span>{t('{count} acuerdo(s) cerrados. Se ejecutarán cuando el mercado abra.', { count: pendingTransfers.length })}</span>
                </div>
              )}
              {offers.length ? <div className="stack-sm">{offers.map((offer) => {
                const affordable = offer.buyer_budget === undefined || offer.buyer_budget >= offer.fee
                return <div className="market-row" key={offer.id}><div className="market-row-main"><b>{offer.player_name}</b><span>{offer.from_club_name} · {offer.from_league || 'Liga'} · {offer.listed ? t('Jugador en venta') : t('Oferta por rendimiento')}</span><span>{money(offer.fee)} de traspaso · {money(offer.salary)} de salario · {offer.years} años · presupuesto comprador {money(offer.buyer_budget || 0)}</span></div><Badge tone={affordable ? 'ok' : 'danger'}>{affordable ? t('Puede pagar') : t('Sin fondos')}</Badge><Button size="sm" variant="primary" icon={Check} onClick={() => offerAction(offer, 'accept')} loading={busy === `offer-${offer.id}`} disabled={!affordable}>{t('Aceptar')}</Button><Button size="sm" variant="danger" icon={X} onClick={() => offerAction(offer, 'reject')} loading={busy === `offer-${offer.id}`}>{t('Rechazar')}</Button></div>
              })}</div> : <EmptyState title={t('Sin ofertas')} body={t('Pon jugadores en venta o espera a que tu rendimiento llame la atención de otros clubes.')} />}
              {pendingTransfers.length > 0 && <div className="stack-sm mt-2">{pendingTransfers.map((pending) => <div className="inbox-item" key={pending.id}><b>{pending.player_name} · {pending.type === 'venta' ? t('venta') : t('fichaje')}</b><span>{pending.type === 'venta' ? t('Salida') : t('Llegada')} · {money(pending.fee)} · {pending.status.replaceAll('_', ' ')}</span><p>{t('Acuerdo cerrado el {date}. Se ejecutará al abrir el mercado.', { date: pending.created })}</p></div>)}</div>}
            </Card>
          )}
        </>
      ))}
    </>
  )
}

function PlayerRow({ player, onOpen }: { player: MarketPlayer; onOpen: () => void }) {
  const { t } = useLanguage()
  return (
    <button className="market-row" type="button" style={{ textAlign: 'left', color: 'inherit' }} onClick={onOpen}>
      <Avatar player={player} size={42} />
      <div className="market-row-main">
        <div className="inline"><b>{player.name}</b>{player.transfer_listed && <Badge tone="gold">{t('En venta')}</Badge>}</div>
        <span>{player.origin_team ? t('Agente libre · procede de {team}', { team: player.origin_team }) : player.owner_name} · {player.league_label} · {player.subposition} · {player.archetype}</span>
        <span>{t('{age} años · {stars} · ojeado {scout}', { age: player.age, stars: player.stars, scout: player.scout })} · {player.apps} PJ · {player.season_goals} G · {player.season_assists} A</span>
      </div>
      <div className="market-row-side"><b>{money(player.asking)}</b><span>{t('salario {value}', { value: money(player.salary) })}</span></div>
      <ArrowRight size={16} className="muted" />
    </button>
  )
}
