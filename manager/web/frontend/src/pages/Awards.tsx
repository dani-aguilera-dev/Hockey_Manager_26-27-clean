import { useEffect, useState } from 'react'
import { Award as AwardIcon, Crown, Star, Trophy } from 'lucide-react'
import { api } from '../lib/api'
import type { AwardsData, SeasonAward } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, StatCard } from '../components/ui'

function AwardCard({ award }: { award: SeasonAward | AwardsData['awards'][number] }) {
  return (
    <div className="award-card">
      <div className="inline" style={{ justifyContent: 'space-between' }}>
        <Badge tone="gold">{award.label}</Badge>
        <b className="gold">{award.value}</b>
      </div>
      <h3>{award.player_name}</h3>
      <p className="small muted">{award.team_name} · {award.position} · {award.age} años · OVR {award.overall}</p>
      <p className="small muted">{award.apps} partidos · {award.goals} goles · {award.assists} asistencias · rating {award.rating.toFixed(2)}</p>
    </div>
  )
}

export default function AwardsPage() {
  const { toast } = useToast()
  const [data, setData] = useState<AwardsData | null>(null)
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api.get<AwardsData>('/awards')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar los premios.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading && !data) return <LoadingBlock label="Contando los votos y las estadísticas…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar los premios.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow={`${data.competition} · ${data.season}`}
        title="Premios y galardones"
        subtitle="MVP, máximo goleador, mejor joven, portero, defensa, once ideal y premios del último partido. Todo sale de estadísticas reales."
        actions={<><Badge tone="gold">{data.awards.length} premios</Badge><Button icon={Trophy} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Temporada" value={data.season} hint={data.competition} icon={Trophy} />
        <StatCard label="Premios individuales" value={data.awards.length} hint="Máximo goleador, MVP, joven, portero y defensa" tone="gold" icon={Crown} />
        <StatCard label="Once ideal" value={data.best_xi.length} hint="4-3-3 por rendimiento" tone="blue" icon={Star} />
        <StatCard label="Premios del partido" value={data.last_match.length} hint="Último partido disputado" icon={AwardIcon} />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">GALARDONES DE LA TEMPORADA</div><h3 style={{ margin: '3px 0 0' }}>Los nombres del curso</h3></div>
          <Crown size={22} className="gold" />
        </div>
        <div className="awards-grid mt-2">
          {data.awards.map((award) => <AwardCard key={award.id} award={award} />)}
          {!data.awards.length && <p className="small muted">Todavía no hay partidos suficientes para entregar premios.</p>}
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Once ideal</h3><Badge tone="blue">4-3-3</Badge></div>
          <div className="stack-sm mt-2">
            {data.best_xi.map((player, index) => (
              <div className="award-xi-row" key={player.player_id}>
                <span>{index + 1}</span><div><b>{player.player_name}</b><small>{player.position} · {player.team_name}</small></div><b className="gold">{player.rating.toFixed(2)}</b>
              </div>
            ))}
            {!data.best_xi.length && <p className="small muted">Sin datos suficientes.</p>}
          </div>
        </Card>
        <Card>
          <h3>Premios del último partido</h3>
          <div className="stack-sm mt-2">
            {data.last_match.map((award) => (
              <div className="award-xi-row" key={award.id}>
                <Badge tone="gold">{award.label}</Badge><div><b>{award.player_name}</b><small>{award.team_name} · {award.metric} {award.value}</small></div>
              </div>
            ))}
            {!data.last_match.length && <p className="small muted">Sin premios de partido.</p>}
          </div>
        </Card>
      </div>

      <Card className="mt-2">
        <h3>Historial de premios</h3>
        <div className="stack-sm mt-2">
          {data.history.map((entry) => (
            <div className="award-history-row" key={`${entry.season}-${entry.competition}`}>
              <Badge tone="neutral">{entry.season} · {entry.competition}</Badge>
              <div><b>{entry.awards.map((award) => `${award.label}: ${award.player_name}`).join(' · ')}</b><span>{entry.best_xi.length} jugadores en el once ideal</span></div>
            </div>
          ))}
          {!data.history.length && <p className="small muted">El historial aparecerá al cerrar la temporada.</p>}
        </div>
      </Card>
    </>
  )
}
