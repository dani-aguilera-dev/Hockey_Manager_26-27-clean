import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Flag, MessageSquare } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money, resultTone } from '../lib/format'
import type { MatchReport } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, LoadingBlock, PageHeader, Progress } from '../components/ui'

export default function ReportPage() {
  const navigate = useNavigate()
  const { game } = useGame()
  const { toast } = useToast()
  const [report, setReport] = useState<MatchReport | null>(game?.last_result || null)
  const [loading, setLoading] = useState(!game?.last_result)

  useEffect(() => {
    if (report) return
    api.get<{ report: MatchReport }>('/match/report')
      .then(({ data }) => setReport(data.report))
      .catch((err) => toast(err instanceof Error ? err.message : 'No hay parte de partido.', 'danger'))
      .finally(() => setLoading(false))
  }, [report, toast])

  if (loading) return <LoadingBlock label="Cargando parte del partido…" />
  if (!report) return <Card><p className="muted">No hay parte de partido.</p><Button onClick={() => navigate('/game')}>Volver al club</Button></Card>

  const tone = resultTone(report.result)
  const cards = report.cards || []
  const injuries = report.injuries || []
  const stats = [
    ['Posesión', `${report.home_stats.possession || 0}%`, `${report.away_stats.possession || 0}%`],
    ['Tiros', report.home_stats.shots || 0, report.away_stats.shots || 0],
    ['A puerta', report.home_stats.shots_on_target || 0, report.away_stats.shots_on_target || 0],
    ['PC', report.home_stats.pc || 0, report.away_stats.pc || 0],
    ['Strokes', report.home_stats.strokes || 0, report.away_stats.strokes || 0],
    ['Paradas', report.home_stats.saves || 0, report.away_stats.saves || 0],
  ]

  return (
    <>
      <PageHeader
        eyebrow={`${report.round ? `Jornada ${report.round}` : 'Partido'} · ${dateLabel(report.date)}`}
        title={report.result}
        subtitle={`${report.home_name} ${report.home_goals}-${report.away_goals} ${report.away_name} · ${report.user_goals} goles a favor · ${report.user_against} en contra`}
        actions={<><Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button>{game?.press?.post_available && <Button icon={MessageSquare} onClick={() => navigate('/game/press/post')}>Rueda posterior</Button>}<Button variant="primary" icon={ArrowRight} onClick={() => navigate('/game/match')}>Próximo partido</Button></>}
      />

      <Card>
        <div className="scoreboard">
          <div className="score-team"><div><h2>{report.home_name}</h2><span className="muted">Local</span></div></div>
          <div><div className="score-value">{report.home_goals} - {report.away_goals}</div><div className="score-meta"><Badge tone={tone}>{report.result}</Badge></div></div>
          <div className="score-team right"><div><h2>{report.away_name}</h2><span className="muted">Visitante</span></div></div>
        </div>
        <div className="match-strip"><span>Asistencia {report.attendance || '—'}</span><span>·</span><span>Gestión {report.home_management?.score || '—'} / {report.away_management?.score || '—'}</span><span>·</span><span>Preparación +{report.prep_bonus || 0}</span>{report.referee?.name && <><span>·</span><span>Árbitro: {report.referee.name} ({report.referee.style})</span></>}</div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <h3>Estadísticas</h3>
          <div className="possession-bar"><span style={{ width: `${report.home_stats.possession || 50}%` }} /><span style={{ width: `${100 - (report.home_stats.possession || 50)}%` }} /></div>
          {stats.map(([label, home, away]) => <div className="stat-line" key={label}><b>{home}</b><span>{label}</span><b className="num">{away}</b></div>)}
        </Card>
        <Card>
          <h3>Gestión</h3>
          <div className="stack-sm">
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Local</span><b>{report.home_management?.score || '—'}/100</b></div><Progress value={report.home_management?.score || 0} tone="gold" /></div>
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Visitante</span><b>{report.away_management?.score || '—'}/100</b></div><Progress value={report.away_management?.score || 0} tone="blue" /></div>
            <p className="small muted">La gestión premia moral, cohesión, descanso, confianza y encaje posicional.</p>
          </div>
          {report.travel && <p className="small muted mt-2">Viaje: {String(report.travel.mode || '—')} · coste {money(Number(report.travel.cost || 0))}</p>}
        </Card>
      </div>

      <Card className="mt-2">
        <h3>Decisiones arbitrales</h3>
        <div className="stack-sm mt-2">
          {[
            ['Ventajas', 'advantage'],
            ['Ventajas fallidas', 'advantage_failed'],
            ['Juego peligroso', 'dangerous_play'],
            ['Juego peligroso sancionado', 'dangerous_sanction'],
            ['Distancia de 5 metros', 'distance_5m'],
            ['Golpe franco +10 m', 'free_hit_10m'],
            ['PC denegados', 'pc_denied'],
            ['PC repetidos', 'pc_retake'],
            ['Goles anulados', 'goals_disallowed'],
            ['Anulados por pie', 'foot_goals_disallowed'],
            ['Anulados por revés', 'back_stick_goals_disallowed'],
            ['Anulados fuera del círculo', 'outside_circle_goals_disallowed'],
            ['Strokes concedidos', 'stroke_awarded'],
            ['Strokes repetidos', 'stroke_retake'],
          ].map(([label, key]) => (
            <div className="stat-line" key={key}><b>{report.home_stats[key] || 0}</b><span>{label}</span><b className="num">{report.away_stats[key] || 0}</b></div>
          ))}
        </div>
        <p className="small muted mt-2">El árbitro puede dejar jugar la ventaja, graduar el juego peligroso, adelantar 10 metros un golpe franco, repetir un PC/stroke por invasión o anular un gol por pie, revés del stick o disparo desde fuera del círculo.</p>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Tiempo añadido</h3><Badge tone="neutral">{Object.values(report.added_time || {}).reduce((sum, value) => sum + Number(value || 0), 0)}′</Badge></div>
        <div className="stack-sm mt-2">
          {[1, 2, 3, 4].map((quarter) => (
            <div className="stat-line" key={quarter}><b>{report.added_time?.[String(quarter)] || 0}′</b><span>{quarter}º cuarto</span><b className="num">{report.added_time?.[String(quarter)] || 0}′</b></div>
          ))}
        </div>
      </Card>

      <Card className="mt-2">
        <h3>Crónica</h3>
        <div className="event-list" style={{ maxHeight: 420 }}>
          {report.events?.length ? report.events.map((event, index) => <div className={`event-row ${event.type}`} key={`${event.minute}-${index}`}><span className="event-minute">{event.minute}'</span><p><b>{event.text}</b></p></div>) : <p className="small muted">Sin eventos registrados.</p>}
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>Parte médico</h3>
            <Badge tone={injuries.length ? 'danger' : 'ok'}>{injuries.length ? `${injuries.length} lesión(es)` : 'Sin lesiones'}</Badge>
          </div>
          {injuries.length ? (
            <div className="stack-sm mt-2">
              {injuries.map((injury, index) => (
                <div className="squad-status-row" key={`${injury.player_id}-${index}`}>
                  <span className="squad-status-main">
                    <b>{injury.player_name || injury.player_id}</b>
                    <span>{injury.team_name || injury.team_id} · {injury.type || 'Lesión'} · {injury.severity}</span>
                  </span>
                  <Badge tone="danger">{injury.matches} partido(s)</Badge>
                </div>
              ))}
            </div>
          ) : <p className="small muted mt-2">El equipo termina sin lesiones nuevas.</p>}
        </Card>
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>Disciplina</h3>
            <Badge tone={cards.length ? 'warn' : 'ok'}>{cards.length ? `${cards.length} tarjeta(s)` : 'Sin tarjetas'}</Badge>
          </div>
          {cards.length ? (
            <div className="stack-sm mt-2">
              {cards.map((card, index) => (
                <div className="squad-status-row" key={`${card.player_id}-${index}`}>
                  <span className="squad-status-main">
                    <b>{card.player_name || card.player_id}</b>
                    <span>{card.team_name || card.team_id} · {card.reason || 'Sanción'} · {card.minute ?? '—'}′</span>
                  </span>
                  <Badge tone={card.type === 'red' ? 'danger' : card.type === 'yellow' ? 'warn' : 'neutral'}>
                    {card.label || card.type}{card.duration_minutes ? ` · ${card.duration_minutes}′` : ''}
                  </Badge>
                </div>
              ))}
            </div>
          ) : <p className="small muted mt-2">El partido termina sin tarjetas.</p>}
        </Card>
      </div>

      <Card className="mt-2">
        <h3>Valoraciones</h3>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th></th><th>Jugador</th><th className="num">Rating</th></tr></thead>
            <tbody>{Object.entries(report.ratings || {}).sort(([, a], [, b]) => b - a).map(([name, rating]) => {
              const player = game?.team.players.find((item) => item.name === name)
              return <tr key={name}><td>{player ? <Avatar player={player} size={24} /> : null}</td><td>{name}</td><td className="num"><Badge tone={rating >= 7 ? 'ok' : rating >= 6 ? 'neutral' : 'danger'}>{rating.toFixed(2)}</Badge></td></tr>
            })}</tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
