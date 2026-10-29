import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, BadgeEuro, ShieldCheck } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { TeamDetailPayload } from '../types'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, Crest, LoadingBlock, PageHeader, StatCard } from '../components/ui'
import { Pitch } from '../components/Pitch'

export default function TeamPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [data, setData] = useState<TeamDetailPayload | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    api.get<TeamDetailPayload>(`/team/${id}`)
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el equipo.', 'danger'))
      .finally(() => setLoading(false))
  }, [id, toast])

  if (loading) return <LoadingBlock label="Cargando equipo…" />
  if (!data) return <Card><p className="muted">No se encontró el equipo.</p><Button onClick={() => navigate('/game/table')}>Volver a la tabla</Button></Card>

  const { team, club } = data
  const coach = team.staff.find((member) => member.role === 'head_coach')

  return (
    <>
      <PageHeader
        eyebrow={`${team.league}${data.group ? ` · Grupo ${data.group}` : ''} · ${team.country}`}
        title={team.name}
        subtitle={`${team.city} · ${team.stadium_name} · ${team.stadium_capacity} localidades · objetivo ${team.board_expectation}`}
        actions={<><Button icon={BadgeEuro} onClick={() => navigate(`/game/market?club_id=${team.id}`)}>Mercado del club</Button><Button icon={ArrowLeft} onClick={() => navigate('/game/table')}>Volver a la tabla</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Posición" value={team.played ? `${data.position}º` : 'Pretemporada'} hint={`${team.points} pts · ${team.played} PJ`} tone="gold" />
        <StatCard label="Balance" value={`${team.won}V ${team.drawn}E ${team.lost}D`} hint={`GF ${team.goals_for} · GC ${team.goals_against}`} />
        <StatCard label="Moral" value={`${team.morale}/20`} hint={`Cohesión ${team.cohesion}/20`} tone="blue" />
        <StatCard label="Academia" value={`${team.academy_rating}/100`} hint={`Objetivo: ${team.board_expectation}`} />
      </div>

      <div className="split-3">
        <Card>
          <h3>Club</h3>
          <p className="small muted">{club.history || 'Sin historia registrada.'}</p>
          <div className="inline"><Crest src={team.crest} name={team.name} size={50} /><div><b>{club.full_name || team.name}</b><div className="small muted">Fundado en {club.founded || '—'}</div></div></div>
          <p className="small muted mt-2">Colores: {club.colors?.length ? club.colors.join(' · ') : '—'}</p>
        </Card>
        <Card>
          <h3>Instalaciones</h3>
          <p><b>{team.stadium_name}</b></p>
          <p className="small muted">{String(club.stadium?.address || 'Dirección no disponible')}</p>
          <p className="small muted">Campos: {String(club.facilities?.pitches || '—')} · Gimnasio: {club.facilities?.gym ? 'sí' : 'no'}</p>
        </Card>
        <Card>
          <h3>Cuerpo técnico</h3>
          {data.is_user ? <div className="squad-status-row"><span className="board-icon">T</span><span className="squad-status-main"><b>Tú</b><span>Entrenador · manager del club</span></span><Badge tone="gold">Manager</Badge></div> : coach && <div className="squad-status-row"><Avatar player={{ name: coach.name, initials: coach.name.slice(0, 2) }} size={32} /><span className="squad-status-main"><b>{coach.name}</b><span>{coach.role_label}</span></span><Badge tone="neutral">{coach.rating}/100</Badge></div>}
          {team.staff.filter((member) => member.role !== 'head_coach').slice(0, 4).map((member) => (
            <div className="squad-status-row" key={member.role}><Avatar player={{ name: member.name, initials: member.name.slice(0, 2) }} size={28} /><span className="squad-status-main"><b>{member.name}</b><span>{member.role_label}</span></span><Badge tone="neutral">{member.rating}</Badge></div>
          ))}
        </Card>
      </div>

      <Card className="mt-2" padded={false}>
        <div style={{ padding: '18px 18px 0' }}><div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">ONCE PROBABLE</div><h3 style={{ margin: '3px 0 0' }}>{data.formation}</h3></div><Badge tone="neutral">{team.name}</Badge></div></div>
        <Pitch rows={data.probable_rows} formation={data.formation} />
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Plantilla</h3><Badge tone="neutral">{team.players.length} jugadores</Badge></div>
        <div className="table-wrap mt-2">
          <table className="data-table">
            <thead><tr><th>Jugador</th><th>Pos</th><th>Nivel</th><th className="num">Edad</th><th className="num">OVR</th><th className="num">PJ</th><th className="num">G</th><th className="num">A</th><th className="num">Rating</th></tr></thead>
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
        <Card><h3>Últimos resultados</h3>{data.played.length ? data.played.map((fixture) => <p className="small" key={fixture.id}>J{fixture.round} · {fixture.home_name} {fixture.home_goals}-{fixture.away_goals} {fixture.away_name}</p>) : <p className="small muted">Sin resultados todavía.</p>}</Card>
        <Card><h3>Próximos partidos</h3>{data.upcoming.length ? data.upcoming.map((fixture) => <p className="small" key={fixture.id}>J{fixture.round} · {dateLabel(fixture.date)} · {fixture.home_name} vs {fixture.away_name}</p>) : <p className="small muted">Sin partidos pendientes.</p>}</Card>
      </div>

      {data.is_user && <div className="actions mt-2"><Button variant="primary" icon={ArrowRight} onClick={() => navigate('/game/match')}>Preparar partido</Button><Button icon={ShieldCheck} onClick={() => navigate('/game/staff')}>Staff y junta</Button></div>}
    </>
  )
}
