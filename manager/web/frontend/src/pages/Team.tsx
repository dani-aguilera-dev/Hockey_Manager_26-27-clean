import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, BadgeEuro, ShieldCheck } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { TeamDetailPayload } from '../types'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../lib/i18n'
import { Avatar, Badge, Button, Card, Crest, LoadingBlock, PageHeader, StatCard } from '../components/ui'
import { Pitch } from '../components/Pitch'

export default function TeamPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [data, setData] = useState<TeamDetailPayload | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    api.get<TeamDetailPayload>(`/team/${id}`)
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : t('No se pudo cargar el equipo.'), 'danger'))
      .finally(() => setLoading(false))
  }, [id, toast])

  if (loading) return <LoadingBlock label={t('Cargando equipo…')} />
  if (!data) return <Card><p className="muted">{t('No se encontró el equipo.')}</p><Button onClick={() => navigate('/game/table')}>{t('Volver a la tabla')}</Button></Card>

  const { team, club } = data
  const coach = team.staff.find((member) => member.role === 'head_coach')

  return (
    <>
      <PageHeader
        eyebrow={`${team.league}${data.group ? ` · ${t('Grupo {group}', { group: data.group })}` : ''} · ${team.country}`}
        title={team.name}
        subtitle={t('{city} · Entrenador: {manager} · {stadium} · {capacity} localidades · objetivo {expectation}', { city: team.city, manager: team.manager_name, stadium: team.stadium_name, capacity: team.stadium_capacity, expectation: team.board_expectation })}
        actions={<><Button icon={BadgeEuro} onClick={() => navigate(`/game/market?club_id=${team.id}`)}>{t('Mercado del club')}</Button><Button icon={ArrowLeft} onClick={() => navigate('/game/table')}>{t('Volver a la tabla')}</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label={t('Posición')} value={team.played ? `${data.position}º` : t('Pretemporada')} hint={t('{points} pts · {played} PJ', { points: team.points, played: team.played })} tone="gold" />
        <StatCard label={t('Balance')} value={`${team.won}V ${team.drawn}E ${team.lost}D`} hint={`GF ${team.goals_for} · GC ${team.goals_against}`} />
        <StatCard label={t('Moral')} value={`${team.morale}/20`} hint={t('Cohesión {value}/20', { value: team.cohesion })} tone="blue" />
        <StatCard label={t('Academia')} value={`${team.academy_rating}/100`} hint={t('Objetivo: {value}', { value: team.board_expectation })} />
      </div>

      <div className="split-3">
        <Card>
          <h3>{t('Club')}</h3>
          <p className="small muted">{club.history || t('Sin historia registrada.')}</p>
          <div className="inline"><Crest src={team.crest} name={team.name} size={50} /><div><b>{club.full_name || team.name}</b><div className="small muted">{t('Fundado en {year}', { year: club.founded || '—' })}</div></div></div>
          <p className="small muted mt-2">{t('Colores: {value}', { value: club.colors?.length ? club.colors.join(' · ') : '—' })}</p>
          <p className="small muted">{t('Ubicación: {value}', { value: [club.city || team.city, club.province, club.community, club.country].filter(Boolean).join(' · ') })}</p>
          <div className="inline mt-1">{club.location_verified ? <Badge tone="ok">{t('Ubicación verificada')}</Badge> : <Badge tone="warn">{t('Ubicación por revisar')}</Badge>}{club.source_url && <a className="small gold" href={club.source_url} target="_blank" rel="noreferrer">{t('Fuente')}</a>}</div>
        </Card>
        <Card>
          <h3>{t('Instalaciones')}</h3>
          <p><b>{team.stadium_name}</b></p>
          <p className="small muted">{String(club.stadium?.address || t('Dirección no disponible'))}</p>
          <p className="small muted">{t('Campos: {pitches} · Gimnasio: {gym}', { pitches: String(club.facilities?.pitches || '—'), gym: club.facilities?.gym ? t('sí') : t('no') })}</p>
        </Card>
        <Card>
          <h3>{t('Cuerpo técnico')}</h3>
          {data.is_user ? <div className="squad-status-row"><span className="board-icon">T</span><span className="squad-status-main"><b>{t('Tú')}</b><span>{t('Entrenador · manager del club')}</span></span><Badge tone="gold">{t('Manager')}</Badge></div> : coach && <div className="squad-status-row"><Avatar player={{ name: coach.name, initials: coach.name.slice(0, 2) }} size={32} /><span className="squad-status-main"><b>{coach.name}</b><span>{coach.role_label}</span></span><Badge tone="neutral">{coach.rating}/100</Badge></div>}
          {team.staff.filter((member) => member.role !== 'head_coach').slice(0, 4).map((member) => (
            <div className="squad-status-row" key={member.role}><Avatar player={{ name: member.name, initials: member.name.slice(0, 2) }} size={28} /><span className="squad-status-main"><b>{member.name}</b><span>{member.role_label}</span></span><Badge tone="neutral">{member.rating}</Badge></div>
          ))}
        </Card>
      </div>

      <Card className="mt-2" padded={false}>
        <div style={{ padding: '18px 18px 0' }}><div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">{t('ONCE PROBABLE')}</div><h3 style={{ margin: '3px 0 0' }}>{data.formation}</h3></div><Badge tone="neutral">{team.name}</Badge></div></div>
        <Pitch rows={data.probable_rows} formation={data.formation} />
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>{t('Plantilla')}</h3><Badge tone="neutral">{t('{count} jugadores', { count: team.players.length })}</Badge></div>
        <div className="table-wrap mt-2">
          <table className="data-table">
            <thead><tr><th>{t('Jugador')}</th><th>{t('Pos')}</th><th>{t('Nivel')}</th><th className="num">{t('Edad')}</th><th className="num">{t('OVR')}</th><th className="num">{t('PJ')}</th><th className="num">{t('G')}</th><th className="num">{t('A')}</th><th className="num">{t('Rating')}</th></tr></thead>
            <tbody>
              {team.players.map((player) => (
                <tr key={player.id} className="clickable-row" onClick={() => navigate(`/game/player/${player.id}`)}>
                  <td><div className="table-team"><Avatar player={player} size={24} /><span>{player.name}</span>{!player.available && <Badge tone="danger">{player.absence_label}</Badge>}</div></td>
                  <td>{player.subposition}</td><td><Badge tone="blue">{player.stars}</Badge></td><td className="num">{player.age}</td><td className="num"><b>{player.overall.toFixed(1)}</b></td><td className="num">{player.apps}</td><td className="num">{player.season_goals}</td><td className="num">{player.season_assists}</td><td className="num">{player.rating.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card><h3>{t('Últimos resultados')}</h3>{data.played.length ? data.played.map((fixture) => <p className="small" key={fixture.id}>J{fixture.round} · {fixture.home_name} {fixture.home_goals}-{fixture.away_goals} {fixture.away_name}</p>) : <p className="small muted">{t('Sin resultados todavía.')}</p>}</Card>
        <Card><h3>{t('Próximos partidos')}</h3>{data.upcoming.length ? data.upcoming.map((fixture) => <p className="small" key={fixture.id}>J{fixture.round} · {dateLabel(fixture.date)} · {fixture.home_name} vs {fixture.away_name}</p>) : <p className="small muted">{t('Sin partidos pendientes.')}</p>}</Card>
      </div>

      {data.is_user && <div className="actions mt-2"><Button variant="primary" icon={ArrowRight} onClick={() => navigate('/game/match')}>{t('Preparar partido')}</Button><Button icon={ShieldCheck} onClick={() => navigate('/game/staff')}>{t('Staff y junta')}</Button></div>}
    </>
  )
}
