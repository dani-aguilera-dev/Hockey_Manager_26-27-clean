import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, CalendarDays, ChevronRight, CircleDollarSign, ClipboardList, Flame, MessageSquare, Newspaper, ShieldCheck, Target, TrendingUp, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money, positionLabel, shortLeague } from '../lib/format'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import type { DailyEvent, GameState } from '../types'
import { Avatar, Badge, Button, Card, Crest, Modal, PageHeader, Progress, SectionTitle, StatCard } from '../components/ui'

export default function Dashboard() {
  const navigate = useNavigate()
  const { game, applyState } = useGame()
  const { toast } = useToast()
  const [busy, setBusy] = useState<string | null>(null)
  const [targetDate, setTargetDate] = useState('')
  const [simulation, setSimulation] = useState<NonNullable<GameState['simulation']> | null>(null)

  if (!game) return null
  const { team, game: meta, competition, table, finance, next_fixture: next } = game
  const position = table.find((row) => row.id === team.id)?.position || 0
  const keyPlayers = [...team.players].sort((a, b) => b.overall - a.overall).slice(0, 3)
  const availableCount = team.players.filter((player) => player.available).length
  const absent = team.players.filter((player) => !player.available).slice(0, 4)
  const pendingChats = game.chat_messages.filter((message) => !message.answered)
  const decisions = game.decisions || []
  const lastFive = table.slice(0, 6)
  const promotion = game.promotion
  const promotionGroup = promotion?.groups?.find((group) => group.team_ids.includes(team.id))
  const promotionFinal = promotion?.final_group
  const isPromotion = meta.phase === 'promotion' && Boolean(promotion)

  async function decide(instanceId: string, choiceId: string) {
    setBusy(`decision-${instanceId}`)
    try {
      const response = await api.post<{ state: GameState }>(`/events/${instanceId}`, { choice: choiceId })
      applyState(response.data.state)
      toast(response.message || 'Decisión tomada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo resolver la decisión.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function simulate(mode: 'day' | 'next_match' | 'date') {
    setBusy(mode)
    try {
      const { data, message } = await api.post<GameState>('/simulate', {
        mode,
        target_date: mode === 'date' ? targetDate : undefined,
      })
      applyState(data)
      setSimulation(data.simulation || null)
      toast(message || 'Calendario actualizado.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo avanzar el calendario.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow={`${competition.name} · ${meta.season}`}
        title="Club HQ"
        subtitle={isPromotion
          ? `${team.name} · Fase de ascenso a DHB · ${promotionGroup?.name || 'Fase Nacional'} · ${dateLabel(meta.date)}.`
          : `${team.name} · Jornada ${meta.round} · ${dateLabel(meta.date)}. La temporada, el vestuario y la próxima decisión en una sola lectura.`}
        actions={
          <>
            <Button variant="secondary" icon={ClipboardList} onClick={() => navigate('/game/tactics')}>Táctica</Button>
            <Button variant="primary" icon={ArrowRight} onClick={() => navigate(next ? '/game/match' : '/game/season-end')}>
              {next ? 'Preparar partido' : 'Fin de temporada'}
            </Button>
          </>
        }
      />

      {meta.live_active && (
        <div className="notice notice-warn" style={{ marginBottom: 14 }}>
          <Flame size={16} />
          <div><b>Partido en directo en curso.</b> Termínalo antes de avanzar la jornada. <button className="link-button" type="button" onClick={() => navigate('/game/live')}>Continuar partido →</button></div>
        </div>
      )}

      {availableCount < 11 && (
        <div className="notice notice-danger" style={{ marginBottom: 14 }}>
          <ShieldCheck size={16} />
          <div><b>Solo tienes {availableCount} jugadores disponibles.</b> El once puede salir incompleto. Revisa la <button className="link-button" type="button" onClick={() => navigate('/game/medical')}>enfermería</button> y valora llamar a la cantera.</div>
        </div>
      )}

      <div className="dashboard-kpis">
        <StatCard label="Posición" value={positionLabel(position)} hint={`${team.points} pts · ${team.played} PJ`} tone="gold" icon={TrendingUp} />
        <StatCard label="Caja" value={money(finance.cash)} hint={`${finance.net >= 0 ? '+' : ''}${money(finance.net)} esta temporada`} tone="ok" icon={CircleDollarSign} />
        <StatCard label="Moral" value={`${team.morale}/20`} hint={`Cohesión ${team.cohesion}/20`} icon={Users} />
        <StatCard label="Mercado" value={game.market.status} hint={`${game.market.offers.length} ofertas recibidas`} tone={game.market.window === 'cerrado' ? 'default' : 'blue'} icon={Target} />
      </div>

      {isPromotion && promotion && (
        <Card className="promotion-dashboard-card">
          <SectionTitle
            title={`Fase de ascenso a DHB · ${promotionGroup?.name || 'Fase Nacional'}`}
            aside={<Badge tone="gold">{promotion.stage === 'final' ? 'Liguilla final' : `Grupo · J${meta.promotion_round || 1}`}</Badge>}
          />
          <p className="small muted">
            {promotion.user_qualified
              ? 'Estás clasificado para la fase nacional. Los dos primeros de la liguilla final ascienden a DHB.'
              : 'La fase nacional se está resolviendo con los clasificados de todas las ligas.'}
          </p>
          {promotionGroup && (
            <div className="table-wrap mt-2">
              <table className="data-table">
                <thead><tr><th>#</th><th>Equipo</th><th className="num">PJ</th><th className="num">DG</th><th className="num">PTS</th></tr></thead>
                <tbody>{promotionGroup.table.map((row) => (
                  <tr key={row.team_id} style={row.team_id === team.id ? { background: 'rgba(255,176,32,.06)' } : undefined}>
                    <td>{row.position}</td>
                    <td><b>{row.team}</b>{row.team_id === team.id && <Badge tone="gold">Tú</Badge>}</td>
                    <td className="num">{row.played}</td>
                    <td className="num">{row.gd > 0 ? '+' : ''}{row.gd}</td>
                    <td className="num"><b>{row.points}</b></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
          {promotionFinal && (
            <p className="small mt-2">
              <b>Fase final:</b> {promotionFinal.table.map((row) => `${row.position}. ${row.team}`).join(' · ')}
            </p>
          )}
          <div className="actions mt-2">
            <Button variant="primary" icon={ArrowRight} onClick={() => navigate('/game/promotion')}>Ver fase completa</Button>
            {next && <Button onClick={() => navigate('/game/match')}>Jugar partido</Button>}
          </div>
        </Card>
      )}

      {decisions.length > 0 && (
        <Card className="decision-panel">
          <SectionTitle
            title="Decisiones pendientes"
            aside={<div className="inline"><Badge tone="warn">{decisions.length} {decisions.length === 1 ? 'decisión' : 'decisiones'}</Badge><Button size="sm" variant="ghost" onClick={() => navigate('/game/decisions')}>Historial</Button></div>}
          />
          <div className="stack-sm">
            {decisions.map((decision) => (
              <article className="decision-item" key={decision.id}>
                <div className="inline">
                  <Badge tone={decision.priority >= 8 ? 'danger' : 'neutral'}>{decision.category}</Badge>
                  <span className="small muted">Caduca {dateLabel(decision.expires_at)}</span>
                </div>
                <h3>{decision.title}</h3>
                <p>{decision.body}</p>
                <div className="decision-options">
                  {decision.choices.map((choice) => (
                    <div className="decision-option" key={choice.id}>
                      <Button
                        size="sm"
                        variant={choice.tone === 'danger' ? 'danger' : choice.tone === 'ok' ? 'primary' : 'secondary'}
                        onClick={() => decide(decision.id, choice.id)}
                        loading={busy === `decision-${decision.id}`}
                      >
                        {choice.label}
                      </Button>
                      {choice.description && <span>{choice.description}</span>}
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </Card>
      )}

      <Modal
        open={Boolean(simulation)}
        title={simulation?.stopped_at_match ? 'Simulación hasta el partido' : simulation?.stopped_at_decision ? 'Decisión pendiente' : 'Resumen de simulación'}
        onClose={() => setSimulation(null)}
        wide
      >
        {simulation && (
          <div className="stack-sm">
            <div className="inline"><Badge tone="gold">{simulation.days} día(s)</Badge><span className="small muted">Hoy {dateLabel(simulation.date || game.game.date)}</span>{simulation.stopped_at_match && <Badge tone="warn">Parado antes del partido</Badge>}{simulation.stopped_at_decision && <Badge tone="danger">Decisión pendiente</Badge>}</div>
            <p className="small muted">El avance se procesa exactamente igual que día a día: eventos, mercado, patrocinios, entrenamiento y estado del club se actualizan en cada fecha.</p>
            {simulation.stopped_at_decision && <div className="notice notice-warn"><b>Hay una decisión esperando.</b> Cierra este resumen y resuélvela en el panel de decisiones del dashboard.</div>}
            <div className="simulation-summary">
              {(simulation.events || []).slice().reverse().map((event: DailyEvent, index: number) => (
                <div className="inbox-item" key={`${event.date}-${event.headline}-${index}`}>
                  <b>{event.headline}</b>
                  <span>{event.category} · {dateLabel(event.date)}{event.league ? ` · ${event.league}` : ''}</span>
                  <p>{event.body}</p>
                </div>
              ))}
              {!simulation.events?.length && <p className="small muted">No han ocurrido eventos nuevos en estos días.</p>}
            </div>
            <div className="inline mt-2"><Badge tone={game.market.offers.length ? 'warn' : 'neutral'}>{game.market.offers.length} ofertas de mercado</Badge><Badge tone="neutral">{game.commercial.offers.length} ofertas comerciales</Badge></div>
            <div className="actions mt-2">
              <Button variant="primary" onClick={() => { setSimulation(null); if (simulation.stopped_at_match) navigate('/game/match') }}>{simulation.stopped_at_match ? 'Ir al partido' : 'Cerrar'}</Button>
            </div>
          </div>
        )}
      </Modal>

      <div className="dashboard-grid">
        <div className="dashboard-main">
          <Card className="calendar-card">
            <div className="inline" style={{ justifyContent: 'space-between' }}>
              <div>
                <div className="cat">CALENDARIO</div>
                <h3 style={{ margin: '3px 0 0' }}>Hoy {dateLabel(meta.date)} · {isPromotion ? 'Fase de ascenso a DHB' : shortLeague(competition.code)}</h3>
              </div>
              {next && <Badge tone={next.date === meta.date ? 'warn' : 'neutral'}>Próximo partido: {dateLabel(next.date)}</Badge>}
            </div>
            <div className="form-row">
              <Button variant="primary" icon={CalendarDays} onClick={() => simulate('day')} loading={busy === 'day'}>Avanzar 1 día</Button>
              <Button icon={ChevronRight} onClick={() => simulate('next_match')} loading={busy === 'next_match'}>Hasta el próximo partido</Button>
              <label className="field" style={{ maxWidth: 160 }}>
                <span>Fecha objetivo</span>
                <input type="date" value={targetDate} min={meta.date} onChange={(event) => setTargetDate(event.target.value)} />
              </label>
              <Button variant="ghost" onClick={() => simulate('date')} disabled={!targetDate} loading={busy === 'date'}>Ir a la fecha</Button>
            </div>
            <p className="small muted" style={{ margin: '8px 0 0' }}>La simulación se detiene antes de jugar el partido. No se salta ningún encuentro.</p>
          </Card>

          <Card className="next-match-card">
            <div className="next-match-top">
              <div>
                <div className="cat">PRÓXIMO PARTIDO</div>
                <div className="next-match-teams">
                  <Crest src={next?.home_crest} name={next?.home_name || 'Local'} size={46} />
                  <div>
                    <b>{next?.home_name || 'Sin partido'}</b>
                    <span> vs. {next?.away_name || '—'}</span>
                  </div>
                  <Crest src={next?.away_crest} name={next?.away_name || 'Visitante'} size={46} />
                </div>
              </div>
              <Badge tone={next?.is_cup ? 'gold' : 'blue'}>{next?.label || 'Pretemporada'}</Badge>
            </div>
            <div className="next-match-meta">{next ? `${dateLabel(next.date)} · ${next.is_cup ? 'Eliminatoria a partido único' : isPromotion ? `Fase de ascenso · ${promotion?.stage === 'final' ? 'Fase final' : `Grupo · J${meta.promotion_round || next.round}`}` : `${competition.short_name} · Jornada ${next.round}`}` : 'No queda ningún partido pendiente.'}</div>
            <div className="inline">
              <Button variant="primary" onClick={() => navigate(next ? '/game/match' : '/game/season-end')}>{next ? 'Ver previa y jugar' : 'Ver fin de temporada'}</Button>
              <Button icon={ClipboardList} onClick={() => navigate('/game/training')}>Entrenar</Button>
              <Button variant="ghost" onClick={() => navigate('/game/tactics')}>Editar once</Button>
            </div>
          </Card>

          <Card>
            <SectionTitle title="La actualidad del club" aside={<Button variant="ghost" size="sm" icon={Newspaper} onClick={() => navigate('/game/news')}>Ver todo</Button>} />
            <div className="news-list">
              {game.news.slice(0, 4).map((item, index) => (
                <article className="news-item" key={`${item.headline}-${index}`}>
                  <div className="news-thumb">
                    {item.crest ? <Crest src={item.crest} name={item.headline} size={34} /> : item.photo_url ? <Avatar player={{ name: item.headline, photo: item.photo_url }} size={34} /> : <Newspaper size={18} />}
                  </div>
                  <div className="news-copy">
                    <div className="cat">{item.category} · {dateLabel(item.date)}</div>
                    <h3>{item.headline}</h3>
                    <p>{item.body}</p>
                  </div>
                </article>
              ))}
            </div>
          </Card>

          <div className="split-2">
            <Card>
              <SectionTitle title="Jugadores clave" aside={<Button variant="ghost" size="sm" onClick={() => navigate('/game/squad')}>Plantilla</Button>} />
              <div className="stack-sm">
                {keyPlayers.map((player) => (
                  <button key={player.id} className="squad-status-row" style={{ background: 'none', border: 0, color: 'inherit', width: '100%', textAlign: 'left' }} onClick={() => navigate(`/game/player/${player.id}`)}>
                    <Avatar player={player} size={34} />
                    <span className="squad-status-main"><b>{player.name}</b><span>{player.subposition} · {player.archetype}</span></span>
                    <Badge tone="gold">{player.overall.toFixed(1)}</Badge>
                  </button>
                ))}
              </div>
            </Card>
            <Card>
              <SectionTitle title="Disponibilidad" aside={<Badge tone={absent.length ? 'warn' : 'ok'}>{absent.length ? `${absent.length} bajas` : 'Todo disponible'}</Badge>} />
              {absent.length ? absent.map((player) => (
                <div className="squad-status-row" key={player.id}>
                  <Avatar player={player} size={30} />
                  <span className="squad-status-main"><b>{player.name}</b><span>{player.subposition}</span></span>
                  <Badge tone="danger">{player.absence_label || 'Baja'}</Badge>
                </div>
              )) : <p className="small muted">No hay lesionados ni sancionados. El grupo está disponible.</p>}
            </Card>
          </div>
        </div>

        <aside className="dashboard-side">
          <Card>
            <SectionTitle title="Clasificación" aside={<Button variant="ghost" size="sm" onClick={() => navigate('/game/table')}>Ver tabla</Button>} />
            <table className="table-mini">
              <tbody>
                {lastFive.map((row, index) => (
                  <tr key={row.id}>
                    <td style={{ width: 20 }} className="muted">{index + 1}</td>
                    <td><div className="table-team"><Crest src={row.crest} name={row.name} size={20} /><b>{row.name}</b></div></td>
                    <td className="num">{row.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card>
            <SectionTitle title="Estado del club" />
            <div className="stack-sm">
              <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Confianza de la junta</span><b className="small">{team.board_confidence}/100</b></div><Progress value={team.board_confidence} tone={team.board_confidence >= 60 ? 'ok' : 'danger'} /></div>
              <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Moral del grupo</span><b className="small">{team.morale}/20</b></div><Progress value={team.morale * 5} tone="gold" /></div>
              <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Cohesión</span><b className="small">{team.cohesion}/20</b></div><Progress value={team.cohesion * 5} tone="blue" /></div>
            </div>
            <div className="inline mt-2">
              <Badge tone={meta.week_trained ? 'ok' : 'warn'}>{meta.week_trained ? 'Entreno planificado' : 'Entreno pendiente'}</Badge>
              <Badge tone="neutral">{game.market.status}</Badge>
            </div>
            <p className="small muted" style={{ margin: '10px 0 0' }}>Objetivo: {team.board_expectation}</p>
          </Card>

          <Card>
            <SectionTitle title="Vestuario" aside={<Badge tone={pendingChats.length ? 'warn' : 'ok'}>{pendingChats.length} pendientes</Badge>} />
            {pendingChats.length ? pendingChats.slice(0, 2).map((message) => (
              <div className="inbox-item" key={message.id}>
                <b>{message.player_name}</b>
                <span>Conversación pendiente · {dateLabel(message.date)}</span>
                <p>{message.text}</p>
                <Button size="sm" variant="primary" onClick={() => navigate('/game/chat')}>Responder</Button>
              </div>
            )) : <p className="small muted">No hay conversaciones pendientes. El grupo está tranquilo.</p>}
            <Button variant="ghost" size="sm" icon={MessageSquare} onClick={() => navigate('/game/chat')} className="mt-1">Abrir vestuario</Button>
          </Card>

          <Card>
            <SectionTitle title="Inbox" />
            <div className="inbox-list">
              {game.inbox.slice(0, 3).map((message, index) => (
                <div className="inbox-item" key={`${message.subject}-${index}`}>
                  <b>{message.subject}</b>
                  <span>{message.from} · {dateLabel(message.date)}</span>
                  <p>{message.body}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <SectionTitle title="Accesos rápidos" />
            <div className="actions">
              <Button size="sm" icon={Users} onClick={() => navigate('/game/squad')}>Plantilla</Button>
              <Button size="sm" icon={ShieldCheck} onClick={() => navigate('/game/staff')}>Staff</Button>
              <Button size="sm" icon={CircleDollarSign} onClick={() => navigate('/game/market')}>Mercado</Button>
              <Button size="sm" icon={Target} onClick={() => navigate('/game/youth')}>Cantera</Button>
            </div>
          </Card>
        </aside>
      </div>
    </>
  )
}
