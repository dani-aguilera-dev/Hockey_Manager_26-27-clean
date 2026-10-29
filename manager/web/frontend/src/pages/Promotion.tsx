import { Navigate, useNavigate } from 'react-router-dom'
import { ArrowRight, Trophy } from 'lucide-react'
import { useGame } from '../context/GameContext'
import { Badge, Button, Card, Crest, PageHeader } from '../components/ui'
import { dateLabel } from '../lib/format'

export default function PromotionPage() {
  const navigate = useNavigate()
  const { game } = useGame()
  if (!game) return null

  if (game.objectives?.system !== 'regional') {
    return <Navigate to="/game/objectives" replace />
  }

  const promotion = game.promotion
  if (!promotion) {
    return (
      <Card>
        <p className="muted">La fase de ascenso todavía no está activa.</p>
        <Button onClick={() => navigate('/game')}>Volver al club</Button>
      </Card>
    )
  }

  const groups = promotion.groups || []
  const finalGroup = promotion.final_group
  const qualified = promotion.qualified || []
  const news = game.news.filter((item) => item.category === 'Ascenso')
  const next = game.next_fixture
  const userGroup = promotion.user_group || ''
  const userInPromotion = promotion.user_qualified || groups.some((group) => group.team_ids.includes(game.team.id))
  const path = promotion.path
  const objectives = path?.objectives || []
  const leagues = path?.leagues || promotion.leagues || []
  const statusTone = (status: string) =>
    status === 'completed' ? 'ok' : status === 'failed' ? 'danger' : status === 'active' ? 'gold' : 'neutral'
  const statusLabel = (status: string) =>
    status === 'completed' ? 'Completado' : status === 'failed' ? 'No conseguido' : status === 'active' ? 'En juego' : 'Pendiente'

  return (
    <>
      <PageHeader
        eyebrow={`${game.game.season} · Fase Nacional`}
        title="Ascenso a DHB"
        subtitle="Cuatro grupos de cuatro equipos, liguilla final a partido único y dos plazas de ascenso."
        actions={
          <Button
            variant="primary"
            icon={ArrowRight}
            onClick={() => navigate(next ? '/game/match' : '/game/season-end')}
          >
            {next ? 'Jugar siguiente partido' : 'Ver fin de temporada'}
          </Button>
        }
      />

      <div className="season-hero">
        <Trophy size={42} className="gold" />
        <div>
          <h1>{userInPromotion ? `Estás en el ${userGroup || 'fase nacional'}` : 'Fase nacional en juego'}</h1>
          <p>
            {promotion.stage === 'final'
              ? 'Liguilla final: los dos primeros ascienden a DHB.'
              : 'Fase de grupos: los cuatro campeones pasan a la liguilla final.'}
            {next ? ` Próximo partido: ${dateLabel(next.date)}.` : ''}
          </p>
        </div>
        <Badge tone={promotion.stage === 'final' ? 'ok' : 'gold'}>
          {promotion.stage === 'final' ? 'Fase final' : 'Grupos'}
        </Badge>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
          <div><div className="cat">CAMINO AL ASCENSO</div><h3 style={{ margin: '3px 0 0' }}>Tus objetivos</h3></div>
          {path && <Badge tone={path.qualified ? 'ok' : 'neutral'}>{path.qualified ? 'Clasificado' : 'En curso'}</Badge>}
        </div>
        <p className="small muted" style={{ margin: '0 0 10px' }}>
          Estado: <b>verde</b> = cumplido · <b>dorado</b> = en juego · <b>rojo</b> = no conseguido · <b>gris</b> = pendiente.
        </p>
        <div className="promotion-objectives">
          {objectives.map((objective, index) => (
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
        {path && (
          <p className="small muted mt-2">
            Tu liga: {path.position}º · objetivo: top {path.target}. La Fase Nacional reparte cuatro grupos y dos plazas de ascenso.
          </p>
        )}
      </Card>

      {next && (
        <Card className="next-match-card mt-2">
          <div className="next-match-top">
            <div>
              <div className="cat">PRÓXIMO PARTIDO DE ASCENSO</div>
              <div className="next-match-teams">
                <Crest src={next.home_crest} name={next.home_name} size={46} />
                <div><b>{next.home_name}</b><span> vs. {next.away_name}</span></div>
                <Crest src={next.away_crest} name={next.away_name} size={46} />
              </div>
            </div>
            <Badge tone="gold">{next.label}</Badge>
          </div>
          <div className="next-match-meta">{dateLabel(next.date)} · {next.phase.startsWith('promotion_final') ? 'Fase final' : 'Fase de grupos'}</div>
          <Button variant="primary" onClick={() => navigate('/game/match')}>Ver previa y jugar</Button>
        </Card>
      )}

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
          <div><div className="cat">OBJETIVO 1 · CLASIFICACIÓN</div><h3 style={{ margin: '3px 0 0' }}>Ligas regionales y plazas de Fase Nacional</h3></div>
          <Badge tone="neutral">{leagues.length} ligas</Badge>
        </div>
        <p className="small muted">Los equipos marcados en dorado ocupan plaza de Fase Nacional en este momento.</p>
        <div className="promotion-groups">
          {leagues.map((league) => {
            const qualifierIds = new Set(league.qualifiers.map((row) => row.team_id))
            return (
              <div className="promotion-group" key={league.code}>
                <div className="inline" style={{ justifyContent: 'space-between' }}>
                  <b>{league.short_name}</b>
                  <Badge tone="gold">Top {league.spots}</Badge>
                </div>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead><tr><th>#</th><th>Equipo</th><th className="num">PTS</th></tr></thead>
                    <tbody>{league.table.map((row) => (
                      <tr key={row.team_id} style={row.team_id === game.team.id ? { background: 'rgba(255,176,32,.06)' } : undefined}>
                        <td>{row.position}</td>
                        <td>{row.team}{qualifierIds.has(row.team_id) && <Badge tone="gold">Fase</Badge>}{row.team_id === game.team.id && <Badge tone="neutral">Tú</Badge>}</td>
                        <td className="num"><b>{row.points}</b></td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
          <div><div className="cat">OBJETIVO 2 · GRUPOS</div><h3 style={{ margin: '3px 0 0' }}>Semifinales y equipos clasificados</h3></div>
          <Badge tone="neutral">{qualified.length} equipos</Badge>
        </div>
        <div className="promotion-groups">
          {groups.map((group) => (
            <div className="promotion-group" key={group.name}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <b>{group.name}</b>
                <Badge tone={group.winner ? 'gold' : 'neutral'}>{group.winner || 'En juego'}</Badge>
              </div>
              <div className="table-wrap">
                <table className="data-table">
                  <thead><tr><th>#</th><th>Equipo</th><th className="num">PJ</th><th className="num">DG</th><th className="num">PTS</th></tr></thead>
                  <tbody>{group.table.map((row) => (
                    <tr key={row.team_id} style={row.team_id === game.team.id ? { background: 'rgba(255,176,32,.06)' } : undefined}>
                      <td>{row.position}</td>
                      <td><div className="table-team"><Crest src={group.teams?.find((team) => team.id === row.team_id)?.crest} name={row.team} size={20} /><b>{row.team}</b>{row.team_id === game.team.id && <Badge tone="gold">Tú</Badge>}</div></td>
                      <td className="num">{row.played}</td>
                      <td className="num">{row.gd > 0 ? '+' : ''}{row.gd}</td>
                      <td className="num"><b>{row.points}</b></td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {finalGroup && (
        <Card className="mt-2">
          <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
            <div><div className="cat">OBJETIVO 3 · FASE FINAL</div><h3 style={{ margin: '3px 0 0' }}>Liguilla por el ascenso</h3></div>
            <Badge tone="ok">2 plazas</Badge>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>#</th><th>Equipo</th><th className="num">PJ</th><th className="num">DG</th><th className="num">PTS</th><th /></tr></thead>
              <tbody>{finalGroup.table.map((row) => (
                <tr key={row.team_id} style={row.team_id === game.team.id ? { background: 'rgba(255,176,32,.06)' } : undefined}>
                  <td>{row.position}</td>
                  <td>{row.team}</td>
                  <td className="num">{row.played}</td>
                  <td className="num">{row.gd > 0 ? '+' : ''}{row.gd}</td>
                  <td className="num"><b>{row.points}</b></td>
                  <td>{promotion.promoted_ids?.includes(row.team_id) ? <Badge tone="ok">Asciende</Badge> : null}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </Card>
      )}

      <Card className="mt-2">
        <div className="cat">NOTICIAS DE ASCENSO</div>
        <div className="news-list">
          {news.length ? news.map((item, index) => (
            <article className="news-item" key={`${item.headline}-${index}`}>
              <div className="news-thumb"><Trophy size={18} /></div>
              <div className="news-copy"><div className="cat">Ascenso · {dateLabel(item.date)}</div><h3>{item.headline}</h3><p>{item.body}</p></div>
            </article>
          )) : <p className="small muted">La actualidad de la fase nacional aparecerá aquí en cuanto haya resultados.</p>}
        </div>
      </Card>
    </>
  )
}
