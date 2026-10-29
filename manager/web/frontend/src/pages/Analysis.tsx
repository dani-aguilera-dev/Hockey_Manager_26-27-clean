import { useEffect, useState } from 'react'
import { BarChart3, CalendarRange, Target, TrendingUp } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { AnalysisData, AnalysisMetrics } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, StatCard } from '../components/ui'

function metricRows(home: AnalysisMetrics | null, away: AnalysisMetrics | null) {
  if (!home || !away) return []
  return [
    ['Posesión', `${home.possession}%`, `${away.possession}%`],
    ['Tiros', home.shots, away.shots],
    ['A tiros', home.shots_on_target, away.shots_on_target],
    ['Penaltis córner', home.pc, away.pc],
    ['Paradas', home.saves, away.saves],
    ['Índice de peligro', home.danger_index, away.danger_index],
  ]
}

export default function AnalysisPage() {
  const { toast } = useToast()
  const [data, setData] = useState<AnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState('')

  function load(fixtureId = '') {
    setLoading(true)
    api.get<AnalysisData>(`/analysis${fixtureId ? `?fixture_id=${encodeURIComponent(fixtureId)}` : ''}`)
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el análisis.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  function selectMatch(fixtureId: string) {
    setSelected(fixtureId)
    load(fixtureId)
  }

  if (loading && !data) return <LoadingBlock label="Analizando el partido…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el análisis.</p></Card>

  if (!data.match || !data.metrics) {
    return (
      <>
        <PageHeader eyebrow="Análisis · datos del motor" title="Análisis de partido" subtitle="Eficiencia, cronología y rendimiento individual." />
        <Card><p className="muted">{data.message || 'No hay un partido para analizar.'}</p><Button onClick={() => load()}>Actualizar</Button></Card>
      </>
    )
  }

  const match = data.match
  const home = data.metrics.home
  const away = data.metrics.away
  const rows = metricRows(home, away)
  const userMetrics = match.user_is_home ? home : away
  const quarters = [1, 2, 3, 4].map((quarter) => ({ quarter, events: data.timeline.filter((event) => event.quarter === quarter) }))

  return (
    <>
      <PageHeader
        eyebrow={`${match.competition} · ${dateLabel(match.date)} · ${match.phase}`}
        title="Análisis de partido"
        subtitle={`${match.home_name} ${match.home_goals}-${match.away_goals} ${match.away_name}. Datos reales del motor: sin xG inventado.`}
        actions={<><Badge tone="blue">{data.source === 'archive' ? 'Archivo' : 'Último partido'}</Badge><Button icon={BarChart3} onClick={() => load(selected)}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Goles" value={userMetrics.goals} hint={`${match.home_name} ${match.home_goals}-${match.away_goals} ${match.away_name}`} tone="gold" icon={Target} />
        <StatCard label="Tiros" value={userMetrics.shots} hint={`${userMetrics.shots_on_target} a puerta`} tone="blue" icon={BarChart3} />
        <StatCard label="Precisión" value={`${userMetrics.accuracy}%`} hint={`Conversión ${userMetrics.goal_conversion}%`} icon={TrendingUp} />
        <StatCard label="PC" value={`${userMetrics.pc_goals}/${userMetrics.pc}`} hint={`Conversión ${userMetrics.pc_conversion}%`} />
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">COMPARATIVA</div><h3 style={{ margin: '3px 0 0' }}>El partido en números</h3></div><BarChart3 size={20} className="gold" /></div>
          <div className="analysis-compare mt-2">
            {rows.map(([label, homeValue, awayValue]) => (
              <div key={label}><b>{homeValue}</b><span>{label}</span><b>{awayValue}</b></div>
            ))}
          </div>
        </Card>
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">EFICIENCIA</div><h3 style={{ margin: '3px 0 0' }}>Aprovechamiento</h3></div><Badge tone="gold">{userMetrics.danger_index}</Badge></div>
          <div className="stack-sm mt-2">
            <div className="analysis-efficiency"><span>Conversión de tiros</span><b>{userMetrics.goal_conversion}%</b></div>
            <div className="analysis-efficiency"><span>Precisión</span><b>{userMetrics.accuracy}%</b></div>
            <div className="analysis-efficiency"><span>Conversión de PC</span><b>{userMetrics.pc_conversion}%</b></div>
            <div className="analysis-efficiency"><span>Paradas del rival</span><b>{away.saves}</b></div>
            <div className="analysis-efficiency"><span>Posesión</span><b>{userMetrics.possession}%</b></div>
          </div>
          <p className="small muted mt-2">El índice de peligro combina tiros a puerta, PC y goles; no es xG.</p>
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Cronología</h3><Badge tone="neutral">{data.timeline.length} eventos</Badge></div>
        <div className="analysis-timeline mt-2">
          {quarters.map(({ quarter, events }) => (
            <div className="analysis-quarter" key={quarter}>
              <div className="analysis-quarter-title">{quarter}º cuarto</div>
              {events.length ? events.map((event, index) => <div className={`event-row ${event.type}`} key={`${event.minute}-${index}`}><span className="event-minute">{event.minute}'</span><p><b>{event.text}</b></p></div>) : <p className="small muted">Sin eventos relevantes.</p>}
            </div>
          ))}
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <h3>Rendimiento individual</h3>
          <div className="table-wrap mt-2">
            <table className="data-table">
              <thead><tr><th>Jugador</th><th>Pos</th><th className="num">Min</th><th className="num">G</th><th className="num">A</th><th className="num">Rating</th></tr></thead>
              <tbody>{data.players.map((player) => <tr key={player.id}><td>{player.name}</td><td>{player.position}</td><td className="num">{player.minutes}</td><td className="num">{player.goals}</td><td className="num">{player.assists}</td><td className="num"><b>{player.rating.toFixed(2)}</b></td></tr>)}</tbody>
            </table>
          </div>
          {!data.players.length && <p className="small muted mt-2">El archivo no guarda ratings individuales de partidos antiguos.</p>}
        </Card>
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Últimos partidos</h3><CalendarRange size={16} className="muted" /></div>
          <div className="stack-sm mt-2">
            {data.recent.map((recent) => (
              <button type="button" className={`analysis-recent ${selected === recent.fixture_id ? 'selected' : ''}`} key={recent.fixture_id} onClick={() => selectMatch(recent.fixture_id)}>
                <span>{dateLabel(recent.date)}</span><b>{recent.home_name}</b><strong>{recent.home_goals}-{recent.away_goals}</strong><b>{recent.away_name}</b>
              </button>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-2">
        <h3>Media de la temporada</h3>
        <div className="analysis-season mt-2">
          <div><span>Partidos</span><b>{data.season.matches}</b></div>
          <div><span>Goles a favor</span><b>{data.season.goals_for}</b></div>
          <div><span>Goles en contra</span><b>{data.season.goals_against}</b></div>
          <div><span>Tiros</span><b>{data.season.shots}</b></div>
          <div><span>A puerta</span><b>{data.season.shots_on_target}</b></div>
          <div><span>PC</span><b>{data.season.pc}</b></div>
          <div><span>Posesión</span><b>{data.season.possession}%</b></div>
        </div>
      </Card>
    </>
  )
}
