import { useEffect, useState } from 'react'
import { BookOpen, CalendarRange, Filter, Trophy, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { HistoryData } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, StatCard } from '../components/ui'

type Tab = 'seasons' | 'competitions' | 'matches' | 'players' | 'records'

const tabs: Array<{ id: Tab; label: string }> = [
  { id: 'seasons', label: 'Temporadas' },
  { id: 'competitions', label: 'Competiciones' },
  { id: 'matches', label: 'Partidos' },
  { id: 'players', label: 'Jugadores' },
  { id: 'records', label: 'Récords' },
]

export default function HistoryPage() {
  const { toast } = useToast()
  const [data, setData] = useState<HistoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('seasons')
  const [season, setSeason] = useState('')
  const [competition, setCompetition] = useState('')
  const [teamId, setTeamId] = useState('')
  const [playerQuery, setPlayerQuery] = useState('')
  const [applied, setApplied] = useState({ season: '', competition: '', teamId: '', playerQuery: '' })

  function load(filters = applied) {
    setLoading(true)
    const params = new URLSearchParams()
    if (filters.season) params.set('season', filters.season)
    if (filters.competition) params.set('competition', filters.competition)
    if (filters.teamId) params.set('team_id', filters.teamId)
    if (filters.playerQuery) params.set('player', filters.playerQuery)
    api.get<HistoryData>(`/history?${params.toString()}`)
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el historial.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load({ season: '', competition: '', teamId: '', playerQuery: '' }) }, [])

  function applyFilters() {
    const filters = { season, competition, teamId, playerQuery }
    setApplied(filters)
    load(filters)
  }

  if (loading && !data) return <LoadingBlock label="Reconstruyendo el historial…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el historial.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Archivo del club · memoria deportiva"
        title="Historial completo"
        subtitle="Temporadas, competiciones, partidos, jugadores y récords. Todo queda guardado en la partida y sobrevive al cambio de temporada."
        actions={<Badge tone="blue">{data.summary.seasons} temporadas · {data.summary.matches} partidos</Badge>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Temporadas" value={data.summary.seasons} hint={`Actual ${data.summary.current_season}`} icon={CalendarRange} />
        <StatCard label="Partidos archivados" value={data.summary.matches} hint="Todas las competiciones" tone="blue" icon={BookOpen} />
        <StatCard label="Jugadores" value={data.summary.players} hint="Con minutos o goles" tone="gold" icon={Users} />
        <StatCard label="Títulos del club" value={data.summary.user_titles} hint={data.summary.current_competition} tone="ok" icon={Trophy} />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">FILTROS</div><h3 style={{ margin: '3px 0 0' }}>Consulta el archivo</h3></div>
          <Filter size={18} className="muted" />
        </div>
        <div className="history-filters mt-2">
          <Field label="Temporada"><select value={season} onChange={(event) => setSeason(event.target.value)}><option value="">Todas</option>{data.options.seasons.map((value) => <option key={value} value={value}>{value}</option>)}</select></Field>
          <Field label="Competición"><select value={competition} onChange={(event) => setCompetition(event.target.value)}><option value="">Todas</option>{data.options.competitions.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></Field>
          <Field label="Equipo"><select value={teamId} onChange={(event) => setTeamId(event.target.value)}><option value="">Todos</option>{data.options.teams.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field>
          <Field label="Jugador"><input value={playerQuery} onChange={(event) => setPlayerQuery(event.target.value)} placeholder="Nombre…" /></Field>
          <Button variant="primary" onClick={applyFilters}>Aplicar filtros</Button>
        </div>
      </Card>

      <div className="history-tabs mt-2">
        {tabs.map((item) => <button type="button" className={`history-tab ${tab === item.id ? 'active' : ''}`} key={item.id} onClick={() => setTab(item.id)}>{item.label}</button>)}
      </div>

      {tab === 'seasons' && (
        <Card className="mt-2">
          <h3>Temporadas</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Temporada</th><th>Competición</th><th className="num">Posición</th><th className="num">Puntos</th><th>Campeón</th><th>Copa</th><th>EHL</th></tr></thead>
              <tbody>{data.seasons.map((row) => {
                const userRow = row.table.find((item) => item.team === row.user_club)
                return <tr key={`${row.season}-${row.competition}`}><td>{row.season}</td><td>{row.competition}</td><td className="num">{row.user_position ?? '—'}</td><td className="num">{userRow?.points ?? '—'}</td><td>{row.champion || '—'}</td><td>{row.cup_winner || '—'}</td><td>{row.ehl_winner || '—'}</td></tr>
              })}</tbody>
            </table>
          </div>
          {!data.seasons.length && <p className="small muted mt-2">La primera temporada todavía está en curso. El historial aparecerá al cerrarla.</p>}
        </Card>
      )}

      {tab === 'competitions' && (
        <Card className="mt-2">
          <h3>Competiciones</h3>
          <div className="stack-sm mt-2">
            {data.competitions.map((row) => (
              <div className="history-competition-row" key={`${row.season}-${row.competition}`}>
                <Badge tone="blue">{row.competition}</Badge>
                <div><b>{row.season} · {row.user_club}</b><span>Posición {row.user_position ?? '—'} · {row.points ?? '—'} puntos · Campeón {row.champion || '—'}</span></div>
                <div className="inline">{row.cup_winner && <Badge tone="gold">Copa {row.cup_winner}</Badge>}{row.ehl_winner && <Badge tone="ok">EHL {row.ehl_winner}</Badge>}</div>
              </div>
            ))}
            {!data.competitions.length && <p className="small muted">Sin competiciones cerradas con los filtros actuales.</p>}
          </div>
        </Card>
      )}

      {tab === 'matches' && (
        <Card className="mt-2">
          <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Partidos</h3><Badge tone="neutral">{data.matches.length}</Badge></div>
          <div className="table-wrap mt-2">
            <table className="data-table">
              <thead><tr><th>Fecha</th><th>Competición</th><th>Local</th><th className="num">Resultado</th><th>Visitante</th><th className="num">Asistencia</th></tr></thead>
              <tbody>{data.matches.map((match) => (
                <tr key={`${match.season}-${match.fixture_id}`}><td>{dateLabel(match.date)}</td><td>{match.competition_name}</td><td>{match.home_name}</td><td className="num"><b>{match.home_goals} - {match.away_goals}</b></td><td>{match.away_name}</td><td className="num">{match.attendance || '—'}</td></tr>
              ))}</tbody>
            </table>
          </div>
          {!data.matches.length && <p className="small muted mt-2">Sin partidos con los filtros actuales.</p>}
        </Card>
      )}

      {tab === 'players' && (
        <Card className="mt-2">
          <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Jugadores</h3><Badge tone="neutral">{data.players.length}</Badge></div>
          <div className="table-wrap mt-2">
            <table className="data-table">
              <thead><tr><th>Jugador</th><th>Equipos</th><th>Temporadas</th><th className="num">Partidos</th><th className="num">Goles</th><th className="num">Asist.</th><th className="num">Rating</th></tr></thead>
              <tbody>{data.players.map((player) => (
                <tr key={player.player_id}><td>{player.name}</td><td>{player.teams.join(' · ')}</td><td>{player.seasons.join(', ')}</td><td className="num">{player.apps}</td><td className="num">{player.goals}</td><td className="num">{player.assists}</td><td className="num">{player.rating.toFixed(2)}</td></tr>
              ))}</tbody>
            </table>
          </div>
          {!data.players.length && <p className="small muted mt-2">Sin jugadores con los filtros actuales.</p>}
        </Card>
      )}

      {tab === 'records' && (
        <div className="history-records mt-2">
          <Card><div className="cat">MÁXIMO GOLEADOR</div>{data.records.top_scorer ? <><h3>{data.records.top_scorer.name}</h3><p className="small muted">{data.records.top_scorer.goals} goles · {data.records.top_scorer.apps} partidos · {data.records.top_scorer.teams.join(' · ')}</p></> : <p className="small muted">Sin datos.</p>}</Card>
          <Card><div className="cat">MÁS PARTIDOS</div>{data.records.most_apps ? <><h3>{data.records.most_apps.name}</h3><p className="small muted">{data.records.most_apps.apps} partidos · {data.records.most_apps.goals} goles</p></> : <p className="small muted">Sin datos.</p>}</Card>
          <Card><div className="cat">MEJOR RATING</div>{data.records.best_rating ? <><h3>{data.records.best_rating.name}</h3><p className="small muted">{data.records.best_rating.rating.toFixed(2)} · {data.records.best_rating.apps} partidos</p></> : <p className="small muted">Sin datos.</p>}</Card>
          <Card><div className="cat">MAYOR VICTORIA</div>{data.records.biggest_win ? <><h3>{data.records.biggest_win.home_name} {data.records.biggest_win.home_goals}-{data.records.biggest_win.away_goals} {data.records.biggest_win.away_name}</h3><p className="small muted">{data.records.biggest_win.season} · {data.records.biggest_win.competition_name}</p></> : <p className="small muted">Sin datos.</p>}</Card>
          <Card><div className="cat">CLUB CON MÁS TÍTULOS</div>{data.records.most_titles[0] ? <><h3>{data.records.most_titles[0].team}</h3><p className="small muted">{data.records.most_titles[0].titles} títulos</p></> : <p className="small muted">Sin datos.</p>}</Card>
          <Card><div className="cat">MEJOR POSICIÓN DEL CLUB</div><h3>{data.records.best_user_finish ? `${data.records.best_user_finish}º` : '—'}</h3><p className="small muted">{data.summary.current_competition}</p></Card>
        </div>
      )}
    </>
  )
}
