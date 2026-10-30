import { useEffect, useState } from 'react'
import { Award, BadgeCheck, CalendarRange, Shield, Star, Trophy, UserRound } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { ManagerProfileData } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

const resultTones: Record<string, 'ok' | 'gold' | 'danger'> = { V: 'ok', E: 'gold', D: 'danger' }

export default function ManagerProfilePage() {
  const { toast } = useToast()
  const [data, setData] = useState<ManagerProfileData | null>(null)
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api.get<ManagerProfileData>('/manager')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el perfil.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading && !data) return <LoadingBlock label="Reconstruyendo la carrera del mánager…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el perfil.</p></Card>

  const { manager, record, current, trophies } = data
  const achieved = data.milestones.filter((milestone) => milestone.achieved).length

  return (
    <>
      <PageHeader
        eyebrow={`${manager.competition} · ${manager.season} · ${manager.formation}`}
        title="Perfil del mánager"
        subtitle={`${manager.name} · ${manager.club}. Carrera, palmarés, hitos y situación actual calculados con los partidos y temporadas guardados.`}
        actions={<><Badge tone="gold">{manager.reputation} · {manager.rating}/100</Badge><Button icon={UserRound} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Partidos" value={record.matches} hint={`${record.wins}V ${record.draws}E ${record.losses}D`} tone="blue" icon={CalendarRange} />
        <StatCard label="Victoria" value={`${record.win_rate}%`} hint={`${record.points_per_match} puntos por partido`} tone="gold" icon={Star} />
        <StatCard label="Goles" value={`${record.goals_for}/${record.goals_against}`} hint={`Diferencia ${record.goal_difference >= 0 ? '+' : ''}${record.goal_difference}`} icon={Shield} />
        <StatCard label="Trofeos" value={trophies.total} hint={`${trophies.league} ligas · ${trophies.cup} copas · ${trophies.promotions} ascensos`} tone="ok" icon={Trophy} />
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">RÉCORD</div><h3 style={{ margin: '3px 0 0' }}>Carrera deportiva</h3></div>
            <BadgeCheck size={22} className="gold" />
          </div>
          <div className="manager-record mt-2">
            <div><span>Victorias</span><b>{record.wins}</b></div>
            <div><span>Empates</span><b>{record.draws}</b></div>
            <div><span>Derrotas</span><b>{record.losses}</b></div>
            <div><span>Goles a favor</span><b>{record.goals_for}</b></div>
            <div><span>Goles en contra</span><b>{record.goals_against}</b></div>
            <div><span>Mejor puesto</span><b>{record.best_finish ? `${record.best_finish}º` : '—'}</b></div>
            <div><span>Mejor puntuación</span><b>{record.best_points ?? '—'}</b></div>
            <div><span>Hitos</span><b>{achieved}/{data.milestones.length}</b></div>
          </div>
        </Card>

        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">SITUACIÓN ACTUAL</div><h3 style={{ margin: '3px 0 0' }}>Club y confianza</h3></div>
            <Badge tone={current.board_confidence >= 60 ? 'ok' : current.board_confidence >= 40 ? 'gold' : 'danger'}>{current.position}º</Badge>
          </div>
          <div className="manager-status mt-2">
            <div><span>Confianza de la junta</span><b>{current.board_confidence}/100</b></div>
            <Progress value={current.board_confidence} tone={current.board_confidence >= 60 ? 'ok' : current.board_confidence >= 40 ? 'gold' : 'danger'} />
            <div><span>Confianza de la afición</span><b>{current.fan_confidence}/100</b></div>
            <Progress value={current.fan_confidence} tone={current.fan_confidence >= 60 ? 'ok' : current.fan_confidence >= 40 ? 'gold' : 'danger'} />
            <div><span>Valoración del mánager</span><b>{current.manager_rating}/100</b></div>
            <Progress value={current.manager_rating} tone="gold" />
          </div>
          <div className="manager-money mt-2">
            <div><span>Caja</span><b>{money(current.budget)}</b></div>
            <div><span>Fichajes</span><b>{money(current.transfer_budget)}</b></div>
            <div><span>Fase</span><b>{current.phase}</b></div>
          </div>
        </Card>
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">PALMARÉS</div><h3 style={{ margin: '3px 0 0' }}>Trofeos y ascensos</h3></div>
            <Award size={22} className="gold" />
          </div>
          <div className="manager-trophies mt-2">
            <div><Trophy size={18} /><span>Ligas</span><b>{trophies.league}</b></div>
            <div><Award size={18} /><span>Copas</span><b>{trophies.cup}</b></div>
            <div><Star size={18} /><span>EHL</span><b>{trophies.ehl}</b></div>
            <div><BadgeCheck size={18} /><span>Ascensos</span><b>{trophies.promotions}</b></div>
          </div>
          <div className="stack-sm mt-2">
            {trophies.details.map((item, index) => (
              <div className="manager-trophy-row" key={`${item.season}-${item.title}-${index}`}>
                <Badge tone="gold">{item.title}</Badge>
                <span>{item.season} · {item.competition}</span>
              </div>
            ))}
            {!trophies.details.length && <p className="small muted">Todavía no hay títulos en la carrera.</p>}
          </div>
        </Card>

        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">HITOS</div><h3 style={{ margin: '3px 0 0' }}>Objetivos de carrera</h3></div>
            <Badge tone="neutral">{achieved}/{data.milestones.length}</Badge>
          </div>
          <div className="manager-milestones mt-2">
            {data.milestones.map((milestone) => (
              <div className={`manager-milestone ${milestone.achieved ? 'achieved' : ''}`} key={milestone.id}>
                <div className="inline" style={{ justifyContent: 'space-between' }}>
                  <b>{milestone.label}</b>
                  <span className="small muted">{milestone.value}/{milestone.target}</span>
                </div>
                <p className="small muted">{milestone.description}</p>
                <Progress value={milestone.progress} tone={milestone.achieved ? 'ok' : 'gold'} />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">TRAYECTORIA</div><h3 style={{ margin: '3px 0 0' }}>Temporadas</h3></div>
          <Badge tone="blue">{data.seasons.length}</Badge>
        </div>
        <div className="table-wrap mt-2">
          <table className="data-table">
            <thead><tr><th>Temporada</th><th>Competición</th><th className="num">Puesto</th><th className="num">Puntos</th><th>Campeón</th><th>Trofeos</th></tr></thead>
            <tbody>{data.seasons.map((season) => (
              <tr key={`${season.season}-${season.competition}`}>
                <td>{season.season}{season.in_progress ? ' · en curso' : ''}</td>
                <td>{season.competition}</td>
                <td className="num">{season.position ?? '—'}</td>
                <td className="num">{season.points ?? '—'}</td>
                <td>{season.champion || '—'}</td>
                <td>{season.trophies.length ? season.trophies.join(' · ') : '—'}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>

      <Card className="mt-2">
        <h3>Últimos partidos</h3>
        <div className="stack-sm mt-2">
          {data.recent.map((match, index) => (
            <div className="manager-recent" key={`${match.date}-${index}`}>
              <Badge tone={resultTones[match.result] || 'neutral'}>{match.result}</Badge>
              <div><b>{match.opponent}</b><span>{match.competition} · {dateLabel(match.date)}</span></div>
              <b>{match.goals_for} - {match.goals_against}</b>
            </div>
          ))}
          {!data.recent.length && <p className="small muted">Todavía no hay partidos dirigidos.</p>}
        </div>
      </Card>
    </>
  )
}
