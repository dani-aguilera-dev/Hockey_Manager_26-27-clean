import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Flag, MessageSquare } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money, resultTone } from '../lib/format'
import type { MatchReport } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../lib/i18n'
import { Avatar, Badge, Button, Card, LoadingBlock, PageHeader, Progress } from '../components/ui'

export default function ReportPage() {
  const navigate = useNavigate()
  const { game } = useGame()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [report, setReport] = useState<MatchReport | null>(game?.last_result || null)
  const [loading, setLoading] = useState(!game?.last_result)

  useEffect(() => {
    if (report) return
    api.get<{ report: MatchReport }>('/match/report')
      .then(({ data }) => setReport(data.report))
      .catch((err) => toast(err instanceof Error ? err.message : t('No hay parte de partido.'), 'danger'))
      .finally(() => setLoading(false))
  }, [report, toast])

  if (loading) return <LoadingBlock label={t('Cargando parte del partido…')} />
  if (!report) return <Card><p className="muted">{t('No hay parte de partido.')}</p><Button onClick={() => navigate('/game')}>{t('Volver al club')}</Button></Card>

  const tone = resultTone(report.result)
  const cards = report.cards || []
  const injuries = report.injuries || []
  const stats = [
    [t('Posesión'), `${report.home_stats.possession || 0}%`, `${report.away_stats.possession || 0}%`],
    [t('Tiros'), report.home_stats.shots || 0, report.away_stats.shots || 0],
    [t('A puerta'), report.home_stats.shots_on_target || 0, report.away_stats.shots_on_target || 0],
    [t('PC'), report.home_stats.pc || 0, report.away_stats.pc || 0],
    [t('Strokes'), report.home_stats.strokes || 0, report.away_stats.strokes || 0],
    [t('Paradas'), report.home_stats.saves || 0, report.away_stats.saves || 0],
  ]

  return (
    <>
      <PageHeader
        eyebrow={`${report.round ? t('Jornada {round}', { round: report.round }) : t('Partido')} · ${dateLabel(report.date)}`}
        title={t(report.result)}
        subtitle={t('{home} {home_goals}-{away_goals} {away} · {for} goles a favor · {against} en contra', { home: report.home_name, home_goals: report.home_goals, away_goals: report.away_goals, away: report.away_name, for: report.user_goals, against: report.user_against })}
        actions={<><Button icon={ArrowLeft} onClick={() => navigate('/game')}>{t('Volver al club')}</Button>{game?.press?.post_available && <Button icon={MessageSquare} onClick={() => navigate('/game/press/post')}>{t('Rueda posterior')}</Button>}<Button variant="primary" icon={ArrowRight} onClick={() => navigate('/game/match')}>{t('Próximo partido')}</Button></>}
      />

      <Card>
        <div className="scoreboard">
          <div className="score-team"><div><h2>{report.home_name}</h2><span className="muted">{t('Local')}</span></div></div>
          <div><div className="score-value">{report.home_goals} - {report.away_goals}</div><div className="score-meta"><Badge tone={tone}>{report.result}</Badge></div></div>
          <div className="score-team right"><div><h2>{report.away_name}</h2><span className="muted">{t('Visitante')}</span></div></div>
        </div>
        <div className="match-strip"><span>{t('Asistencia {value}', { value: report.attendance || '—' })}</span><span>·</span><span>{t('Gestión {home} / {away}', { home: report.home_management?.score || '—', away: report.away_management?.score || '—' })}</span><span>·</span><span>{t('Preparación +{value}', { value: report.prep_bonus || 0 })}</span>{report.referee?.name && <><span>·</span><span>{t('Árbitro: {name} ({style})', { name: report.referee.name, style: t(report.referee.style || '') })}</span></>}</div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <h3>{t('Estadísticas')}</h3>
          <div className="possession-bar"><span style={{ width: `${report.home_stats.possession || 50}%` }} /><span style={{ width: `${100 - (report.home_stats.possession || 50)}%` }} /></div>
          {stats.map(([label, home, away]) => <div className="stat-line" key={label}><b>{home}</b><span>{label}</span><b className="num">{away}</b></div>)}
        </Card>
        <Card>
          <h3>{t('Gestión')}</h3>
          <div className="stack-sm">
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Local')}</span><b>{report.home_management?.score || '—'}/100</b></div><Progress value={report.home_management?.score || 0} tone="gold" /></div>
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Visitante')}</span><b>{report.away_management?.score || '—'}/100</b></div><Progress value={report.away_management?.score || 0} tone="blue" /></div>
            <p className="small muted">{t('La gestión premia moral, cohesión, descanso, confianza y encaje posicional.')}</p>
          </div>
          {report.travel && <p className="small muted mt-2">{t('Viaje: {mode} · coste {cost}', { mode: String(report.travel.mode || '—'), cost: money(Number(report.travel.cost || 0)) })}</p>}
        </Card>
      </div>

      <Card className="mt-2">
        <h3>{t('Decisiones arbitrales')}</h3>
        <div className="stack-sm mt-2">
          {[
            [t('Ventajas'), 'advantage'],
            [t('Ventajas fallidas'), 'advantage_failed'],
            [t('Juego peligroso'), 'dangerous_play'],
            [t('Juego peligroso sancionado'), 'dangerous_sanction'],
            [t('Distancia de 5 metros'), 'distance_5m'],
            [t('Golpe franco +10 m'), 'free_hit_10m'],
            [t('PC denegados'), 'pc_denied'],
            [t('PC repetidos'), 'pc_retake'],
            [t('Goles anulados'), 'goals_disallowed'],
            [t('Anulados por pie'), 'foot_goals_disallowed'],
            [t('Anulados por revés'), 'back_stick_goals_disallowed'],
            [t('Anulados por mano/brazo'), 'hand_goals_disallowed'],
            [t('Anulados fuera del círculo'), 'outside_circle_goals_disallowed'],
            [t('Strokes concedidos'), 'stroke_awarded'],
            [t('Strokes repetidos'), 'stroke_retake'],
          ].map(([label, key]) => (
            <div className="stat-line" key={key}><b>{report.home_stats[key] || 0}</b><span>{label}</span><b className="num">{report.away_stats[key] || 0}</b></div>
          ))}
        </div>
        <p className="small muted mt-2">{t('El árbitro puede dejar jugar la ventaja, graduar el juego peligroso, adelantar 10 metros un golpe franco, repetir un PC/stroke por invasión o anular un gol por pie, revés del stick, mano/brazo o disparo desde fuera del círculo.')}</p>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>{t('Tiempo añadido')}</h3><Badge tone="neutral">{Object.values(report.added_time || {}).reduce((sum, value) => sum + Number(value || 0), 0)}′</Badge></div>
        <div className="stack-sm mt-2">
          {[1, 2, 3, 4].map((quarter) => (
            <div className="stat-line" key={quarter}><b>{report.added_time?.[String(quarter)] || 0}′</b><span>{t('{quarter}º cuarto', { quarter })}</span><b className="num">{report.added_time?.[String(quarter)] || 0}′</b></div>
          ))}
        </div>
      </Card>

      <Card className="mt-2">
        <h3>{t('Crónica')}</h3>
        <div className="event-list" style={{ maxHeight: 420 }} role="region" aria-label={t('Crónica del partido')} tabIndex={0}>
          {report.events?.length ? report.events.map((event, index) => <div className={`event-row ${event.type}`} key={`${event.minute}-${index}`}><span className="event-minute">{event.minute}'</span><p><b>{event.text}</b></p></div>) : <p className="small muted">{t('Sin eventos registrados.')}</p>}
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>{t('Parte médico')}</h3>
            <Badge tone={injuries.length ? 'danger' : 'ok'}>{injuries.length ? t('{count} lesión(es)', { count: injuries.length }) : t('Sin lesiones')}</Badge>
          </div>
          {injuries.length ? (
            <div className="stack-sm mt-2">
              {injuries.map((injury, index) => (
                <div className="squad-status-row" key={`${injury.player_id}-${index}`}>
                  <span className="squad-status-main">
                    <b>{injury.player_name || injury.player_id}</b>
                    <span>{injury.team_name || injury.team_id} · {t(injury.type || 'Lesión')} · {t(injury.severity)}</span>
                  </span>
                  <Badge tone="danger">{t('{count} partido(s)', { count: injury.matches })}</Badge>
                </div>
              ))}
            </div>
          ) : <p className="small muted mt-2">{t('El equipo termina sin lesiones nuevas.')}</p>}
        </Card>
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>{t('Disciplina')}</h3>
            <Badge tone={cards.length ? 'warn' : 'ok'}>{cards.length ? t('{count} tarjeta(s)', { count: cards.length }) : t('Sin tarjetas')}</Badge>
          </div>
          {cards.length ? (
            <div className="stack-sm mt-2">
              {cards.map((card, index) => (
                <div className="squad-status-row" key={`${card.player_id}-${index}`}>
                  <span className="squad-status-main">
                    <b>{card.player_name || card.player_id}</b>
                    <span>{card.team_name || card.team_id} · {t(card.reason || 'Sanción')} · {card.minute ?? '—'}′</span>
                  </span>
                  <Badge tone={card.type === 'red' ? 'danger' : card.type === 'yellow' ? 'warn' : 'neutral'}>
                    {t(card.label || card.type)}{card.duration_minutes ? ` · ${card.duration_minutes}′` : ''}
                  </Badge>
                </div>
              ))}
            </div>
          ) : <p className="small muted mt-2">{t('El partido termina sin tarjetas.')}</p>}
        </Card>
      </div>

      <Card className="mt-2">
        <h3>{t('Valoraciones')}</h3>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th></th><th>{t('Jugador')}</th><th className="num">{t('Rating')}</th></tr></thead>
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
