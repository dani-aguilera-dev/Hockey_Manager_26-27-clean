import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, ClipboardList, Filter } from 'lucide-react'
import { useGame } from '../context/GameContext'
import { positionLabel } from '../lib/format'
import { useLanguage } from '../lib/i18n'
import { Avatar, Badge, Button, Card, PageHeader, Progress, StatCard } from '../components/ui'

const groups = ['Todos', 'Portero', 'Defensa', 'Medio', 'Delantero'] as const
type Group = typeof groups[number]

export default function Squad() {
  const navigate = useNavigate()
  const { game } = useGame()
  const { t } = useLanguage()
  const [group, setGroup] = useState<Group>('Todos')

  if (!game) return null
  const team = game.team
  const players = useMemo(
    () => [...team.players].sort((a, b) => (a.position_group === b.position_group ? b.overall - a.overall : a.position_group.localeCompare(b.position_group))),
    [team.players],
  )
  const filtered = group === 'Todos' ? players : players.filter((player) => player.position_group === group)
  const position = game.table.find((row) => row.id === team.id)?.position || 0
  const available = team.players.filter((player) => player.available).length

  return (
    <>
      <PageHeader
        eyebrow={`${game.competition.short_name} · ${game.game.season}`}
        title={t('Plantilla')}
        subtitle={t('{count} fichas · {available} disponibles · gestión {score}/100. La plantilla, ordenada para decidir.', {
          count: team.players.length,
          available,
          score: team.management_score.toFixed(0),
        })}
        actions={<Button variant="primary" icon={ClipboardList} onClick={() => navigate('/game/tactics')}>{t('Editar once')}</Button>}
      />

      <div className="dashboard-kpis">
        <StatCard label={t('Posición')} value={positionLabel(position)} hint={t('{points} pts · {played} PJ', { points: team.points, played: team.played })} tone="gold" />
        <StatCard label={t('Disponibles')} value={`${available}/${team.players.length}`} hint={t('{count} bajas', { count: team.players.length - available })} tone={available === team.players.length ? 'ok' : 'danger'} />
        <StatCard label={t('Masa salarial')} value={`${Math.round(team.player_wage_bill / 1000)} K €`} hint={t('Salarios de jugadores')} />
        <StatCard label={t('Moral media')} value={`${(team.players.reduce((sum, p) => sum + p.morale, 0) / Math.max(1, team.players.length)).toFixed(1)}/20`} hint={t('Cohesión {value}/20', { value: team.cohesion })} />
      </div>

      <Card>
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
          <div className="inline"><Filter size={15} className="muted" /><span className="small muted">{t('Filtrar por línea')}</span></div>
          <div className="tabs">
            {groups.map((item) => (
              <button key={item} type="button" className={`tab ${group === item ? 'active' : ''}`} onClick={() => setGroup(item)}>
                {t(item)}
                <span>{item === 'Todos' ? team.players.length : team.players.filter((p) => p.position_group === item).length}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="player-grid">
          {filtered.map((player) => (
            <button key={player.id} className="player-card" type="button" style={{ textAlign: 'left', color: 'inherit' }} onClick={() => navigate(`/game/player/${player.id}`)}>
              <Avatar player={player} size={48} />
              <div className="player-card-body">
                <div className="inline" style={{ justifyContent: 'space-between', gap: 6 }}>
                  <span className="player-card-name">{player.name}</span>
                  <Badge tone={player.available ? 'gold' : 'danger'}>{player.overall.toFixed(1)}</Badge>
                </div>
                <div className="player-card-tags"><span>{player.subposition}</span><span className="arch">{player.archetype}</span>{player.perfil !== 'Jugador' && <Badge tone="neutral">{player.perfil}</Badge>}{player.transfer_listed && <Badge tone="gold">{t('En venta')}</Badge>}</div>
                <div className="player-card-meta"><span><b>{player.age}</b> {t('años')}</span><span>{player.stars} ★</span><span>{t('Forma {value}', { value: player.form.toFixed(1) })}</span><span>{t('Rel {value}', { value: player.relationship })}</span></div>
                <div className="inline" style={{ justifyContent: 'space-between', marginTop: 3 }}>
                  <span className="player-card-sub">{player.contract_until} · {Math.round(player.salary / 1000)} K €</span>
                  {player.available ? <Badge tone="ok">{t('Disponible')}</Badge> : <Badge tone="danger">{t(player.absence_label || 'Baja')}</Badge>}
                </div>
                <Progress value={player.fatigue} tone={player.fatigue > 60 ? 'danger' : player.fatigue > 35 ? 'gold' : 'ok'} />
              </div>
            </button>
          ))}
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <h3>{t('Lectura rápida')}</h3>
          <p className="small muted">{t('La ficha muestra el overall absoluto y las estrellas relativas a la categoría. Un 4,5★ en DHB puede ser un 3★ en DHA.')}</p>
          <div className="actions mt-1"><Button size="sm" onClick={() => navigate('/game/table')}>{t('Clasificación')}</Button><Button size="sm" variant="ghost" icon={ArrowRight} onClick={() => navigate('/game/market')}>{t('Reforzar plantilla')}</Button></div>
        </Card>
        <Card>
          <h3>{t('Bajas y sanciones')}</h3>
          {team.players.filter((player) => !player.available).length ? team.players.filter((player) => !player.available).map((player) => (
            <div className="squad-status-row" key={player.id}>
              <Avatar player={player} size={28} />
              <span className="squad-status-main">
                <b>{player.name}</b>
                <span>
                  {player.injury > 0
                    ? `${t(player.injury_type || 'Lesión')} · ${t(player.injury_severity || 'leve')} · ${t('{count} partido(s)', { count: player.injury })}`
                    : `${t(player.suspension_reason || 'Sanción')} · ${t('{count} partido(s)', { count: player.suspension })}`}
                </span>
              </span>
              <Badge tone="danger">{t(player.absence_label || 'Baja')}</Badge>
            </div>
          )) : <p className="small muted">{t('Sin bajas. El cuerpo técnico tiene a toda la plantilla disponible.')}</p>}
        </Card>
      </div>
    </>
  )
}
