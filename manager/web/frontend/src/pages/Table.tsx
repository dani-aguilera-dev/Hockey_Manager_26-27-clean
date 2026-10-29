import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { Competition, Fixture, TeamSummary } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Crest, LoadingBlock, PageHeader } from '../components/ui'

interface LeagueOption {
  code: string
  name: string
  short_name: string
  country: string
  teams: number
}

interface TablePayload {
  competition: Competition
  table: TeamSummary[]
  fixtures: Fixture[]
  leagues: LeagueOption[]
}

export default function TablePage() {
  const navigate = useNavigate()
  const { game } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<TablePayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [round, setRound] = useState('current')
  const [league, setLeague] = useState('')

  useEffect(() => {
    setLeague(game?.game.competition || '')
  }, [game?.game.competition])

  useEffect(() => {
    if (!league) return
    setLoading(true)
    api.get<TablePayload>(`/table?league=${encodeURIComponent(league)}`)
      .then(({ data }) => {
        setData(data)
        setRound('current')
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la clasificación.', 'danger'))
      .finally(() => setLoading(false))
  }, [league, toast])

  const selectedRound = round === 'current' ? String(game?.game.round || 'all') : round
  const fixtures = useMemo(() => {
    if (!data) return []
    return selectedRound === 'all' ? data.fixtures : data.fixtures.filter((fixture) => String(fixture.round) === selectedRound)
  }, [data, selectedRound])

  const rounds = useMemo(() => Array.from(new Set((data?.fixtures || []).map((fixture) => fixture.round))).sort((a, b) => a - b), [data])

  if (loading) return <LoadingBlock label="Cargando clasificación y calendario…" />
  if (!data || !game) return <Card><p className="muted">No se pudo cargar la competición.</p></Card>

  const promotion = game.promotion
  const promotionGroups = promotion?.groups || []
  const finalGroup = promotion?.final_group

  return (
    <>
      <PageHeader
        eyebrow={`${data.competition.country} · ${data.competition.confederation}`}
        title="Clasificación y calendario"
        subtitle={`${data.competition.name} · ${data.table.length} equipos · ${data.fixtures.length} partidos de liga regular.`}
        actions={
          <>
            <select value={league} onChange={(event) => setLeague(event.target.value)} style={{ maxWidth: 280 }}>
              {data.leagues.map((item) => (
                <option key={item.code} value={item.code}>{item.country} · {item.short_name} ({item.teams})</option>
              ))}
            </select>
            <Button icon={ArrowRight} onClick={() => navigate('/game/match')}>Próximo partido</Button>
          </>
        }
      />

      {promotion && game.game.phase === 'promotion' && (
        <Card className="mt-2">
          <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
            <div><div className="cat">FASE NACIONAL</div><h3 style={{ margin: '3px 0 0' }}>Ascenso a DHB</h3></div>
            <Badge tone="gold">{promotion.stage === 'groups' ? 'Grupos' : 'Fase final'}</Badge>
          </div>
          <p className="small muted">Liguillas a partido único. Los dos primeros de la fase final ascienden.</p>
          <div className="promotion-groups">
            {promotionGroups.map((group) => (
              <div className="promotion-group" key={group.name}>
                <div className="inline" style={{ justifyContent: 'space-between' }}>
                  <b>{group.name}</b>
                  <Badge tone="neutral">{group.winner_id ? 'Campeón de grupo' : 'En juego'}</Badge>
                </div>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead><tr><th>#</th><th>Equipo</th><th className="num">PTS</th><th className="num">DG</th></tr></thead>
                    <tbody>{group.table.map((row) => (
                      <tr key={row.team_id} style={row.team_id === game.team.id ? { background: 'rgba(255,176,32,.06)' } : undefined}>
                        <td>{row.position}</td>
                        <td>{row.team}{row.team_id === game.team.id && <Badge tone="gold">Tú</Badge>}</td>
                        <td className="num">{row.points}</td>
                        <td className="num">{row.gd > 0 ? '+' : ''}{row.gd}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
          {finalGroup && (
            <div className="promotion-final mt-2">
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <b>Fase final</b>
                <Badge tone="ok">2 plazas de ascenso</Badge>
              </div>
              <div className="table-wrap">
                <table className="data-table">
                  <thead><tr><th>#</th><th>Equipo</th><th className="num">PTS</th><th className="num">DG</th><th /></tr></thead>
                  <tbody>{finalGroup.table.map((row) => (
                    <tr key={row.team_id} style={row.team_id === game.team.id ? { background: 'rgba(255,176,32,.06)' } : undefined}>
                      <td>{row.position}</td>
                      <td>{row.team}</td>
                      <td className="num">{row.points}</td>
                      <td className="num">{row.gd > 0 ? '+' : ''}{row.gd}</td>
                      <td>{promotion.promoted_ids?.includes(row.team_id) ? <Badge tone="ok">Asciende</Badge> : null}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
          <div className="actions mt-2">
            <Button variant="primary" onClick={() => navigate('/game/match')}>Jugar siguiente partido</Button>
          </div>
        </Card>
      )}

      <Card>
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
          <div><div className="cat">CLASIFICACIÓN</div><h3 style={{ margin: '3px 0 0' }}>{data.competition.short_name}</h3></div>
          <Badge tone="gold">J{game.game.round}</Badge>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>#</th><th>Equipo</th><th className="num">PJ</th><th className="num">G</th><th className="num">E</th><th className="num">P</th><th className="num">GF</th><th className="num">GC</th><th className="num">DG</th><th className="num">PTS</th></tr></thead>
            <tbody>
              {data.table.map((team) => (
                <tr key={team.id} className="clickable-row" onClick={() => navigate(`/game/team/${team.id}`)} style={team.id === game.team.id ? { background: 'rgba(255,176,32,.06)' } : undefined}>
                  <td>{team.position}</td>
                  <td><div className="table-team"><Crest src={team.crest} name={team.name} size={24} /><b>{team.name}</b>{team.id === game.team.id && <Badge tone="gold">Tú</Badge>}</div></td>
                  <td className="num">{team.played}</td><td className="num">{team.won}</td><td className="num">{team.drawn}</td><td className="num">{team.lost}</td><td className="num">{team.goals_for}</td><td className="num">{team.goals_against}</td><td className="num">{team.goal_difference > 0 ? '+' : ''}{team.goal_difference}</td><td className="num"><b>{team.points}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
          <div><div className="cat">CALENDARIO</div><h3 style={{ margin: '3px 0 0' }}>Resultados y próximos partidos</h3></div>
          <select value={round} onChange={(event) => setRound(event.target.value)} style={{ maxWidth: 170 }}>
            <option value="current">Jornada actual</option>
            <option value="all">Todas las jornadas</option>
            {rounds.map((value) => <option key={value} value={value}>Jornada {value}</option>)}
          </select>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>J</th><th>Fecha</th><th>Partido</th><th>Resultado</th><th /></tr></thead>
            <tbody>
              {fixtures.map((fixture) => (
                <tr key={fixture.id}>
                  <td>{fixture.round}</td>
                  <td className="small muted">{dateLabel(fixture.date)}</td>
                  <td><div className="table-team"><Crest src={fixture.home_crest} name={fixture.home_name} size={20} /><span>{fixture.home_name}</span><span className="muted">vs</span><Crest src={fixture.away_crest} name={fixture.away_name} size={20} /><span>{fixture.away_name}</span></div></td>
                  <td><b>{fixture.played ? `${fixture.home_goals}-${fixture.away_goals}` : '—'}</b></td>
                  <td><Button size="sm" variant="ghost" onClick={() => navigate(`/game/team/${fixture.home_id}`)}>Ver</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
