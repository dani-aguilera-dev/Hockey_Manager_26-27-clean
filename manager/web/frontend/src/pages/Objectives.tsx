import { useNavigate } from 'react-router-dom'
import { ArrowRight, Target } from 'lucide-react'
import { useGame } from '../context/GameContext'
import { Badge, Button, Card, Crest, PageHeader } from '../components/ui'
import { dateLabel } from '../lib/format'

export default function ObjectivesPage() {
  const navigate = useNavigate()
  const { game } = useGame()
  if (!game) return null

  const objectives = game.objectives
  const list = objectives?.objectives || []
  const next = game.next_fixture
  const isRegional = objectives?.system === 'regional'
  const statusTone = (status: string) =>
    status === 'completed' ? 'ok' : status === 'failed' ? 'danger' : status === 'active' ? 'gold' : 'neutral'
  const statusLabel = (status: string) =>
    status === 'completed' ? 'Completado' : status === 'failed' ? 'No conseguido' : status === 'active' ? 'En juego' : 'Pendiente'

  return (
    <>
      <PageHeader
        eyebrow={`${game.competition.name} · ${game.game.season}`}
        title={objectives?.title || 'Objetivos'}
        subtitle="El camino del club, objetivo a objetivo. Verde es cumplido; dorado, en juego; rojo, no conseguido."
        actions={
          <Button variant="primary" icon={ArrowRight} onClick={() => navigate(next ? '/game/match' : '/game/season-end')}>
            {next ? 'Jugar siguiente partido' : 'Ver fin de temporada'}
          </Button>
        }
      />

      <div className="season-hero">
        <Target size={42} className="gold" />
        <div>
          <h1>{game.team.name}</h1>
          <p>{game.competition.short_name} · {game.game.phase === 'season_end' ? 'Temporada terminada' : `Jornada ${game.game.round}`}</p>
        </div>
        <Badge tone={list.some((objective) => objective.status === 'completed') ? 'ok' : 'neutral'}>
          {list.filter((objective) => objective.status === 'completed').length}/{list.length} objetivos
        </Badge>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
          <div><div className="cat">OBJETIVOS DE LA TEMPORADA</div><h3 style={{ margin: '3px 0 0' }}>{objectives?.title || 'Objetivos'}</h3></div>
          {isRegional && <Button size="sm" onClick={() => navigate('/game/promotion')}>Ver fase de ascenso</Button>}
        </div>
        <div className="promotion-objectives">
          {list.map((objective, index) => (
            <div className={`promotion-objective status-${objective.status}`} key={objective.key}>
              <div className="promotion-objective-head">
                <span className="promotion-objective-number">{index + 1}</span>
                <Badge tone={statusTone(objective.status)}>{statusLabel(objective.status)}</Badge>
              </div>
              <b>{objective.title}</b>
              <p>{objective.description}</p>
              <p className="promotion-objective-state">{objective.state_text || objective.detail}</p>
              <span className="small muted">{objective.detail}</span>
            </div>
          ))}
        </div>
        {!list.length && <p className="small muted">No hay objetivos definidos para esta competición.</p>}
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
          <div><div className="cat">SITUACIÓN</div><h3 style={{ margin: '3px 0 0' }}>Clasificación actual</h3></div>
          <Badge tone="neutral">{game.table.length} equipos</Badge>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>#</th><th>Equipo</th><th className="num">PJ</th><th className="num">DG</th><th className="num">PTS</th></tr></thead>
            <tbody>{game.table.map((row) => (
              <tr key={row.id} style={row.id === game.team.id ? { background: 'rgba(255,176,32,.06)' } : undefined}>
                <td>{row.position}</td>
                <td><div className="table-team"><Crest src={row.crest} name={row.name} size={20} /><b>{row.name}</b>{row.id === game.team.id && <Badge tone="gold">Tú</Badge>}</div></td>
                <td className="num">{row.played}</td>
                <td className="num">{row.goal_difference > 0 ? '+' : ''}{row.goal_difference}</td>
                <td className="num"><b>{row.points}</b></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>

      {next && (
        <Card className="next-match-card mt-2">
          <div className="next-match-top">
            <div>
              <div className="cat">PRÓXIMO PARTIDO</div>
              <div className="next-match-teams">
                <Crest src={next.home_crest} name={next.home_name} size={46} />
                <div><b>{next.home_name}</b><span> vs. {next.away_name}</span></div>
                <Crest src={next.away_crest} name={next.away_name} size={46} />
              </div>
            </div>
            <Badge tone="blue">{next.label}</Badge>
          </div>
          <div className="next-match-meta">{dateLabel(next.date)} · {game.competition.short_name}</div>
          <Button variant="primary" onClick={() => navigate('/game/match')}>Ver previa y jugar</Button>
        </Card>
      )}
    </>
  )
}
