import { useEffect, useState } from 'react'
import { ArrowUpCircle, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import type { Player, YouthPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, EmptyState, LoadingBlock, PageHeader, Progress } from '../components/ui'

export default function YouthPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<YouthPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)

  function load() {
    setLoading(true)
    api.get<YouthPayload>('/youth')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la cantera.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function action(player: Player, kind: 'promote' | 'release') {
    setBusy(`${kind}-${player.id}`)
    try {
      const response = await api.post<{ state: unknown }>(`/youth/${kind}/${player.id}`)
      applyState(response.data.state as never)
      toast(response.message || (kind === 'promote' ? 'Jugador promocionado.' : 'Jugador liberado.'), 'success')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo completar la acción.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Cargando cantera…" />
  if (!data) return <Card><p className="muted">No se pudo cargar la cantera.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow={`Academia ${data.team.academy_rating}/100`}
        title="Cantera"
        subtitle={`${data.team.youth.length} juveniles · ${data.team.community || 'comunidad del club'} · Sub-16, Sub-18 y Sub-21.`}
        actions={<Badge tone="gold">{data.team.youth.length} fichas</Badge>}
      />

      <Card>
        <div className="dashboard-kpis" style={{ gridTemplateColumns: `repeat(${Math.max(1, data.groups.length)}, minmax(0, 1fr))`, marginBottom: 0 }}>
          {data.groups.map((group) => (
            <div className="stat-card" key={group.category}><span className="stat-top">{group.label}</span><strong>{group.players.length}</strong><small>{group.ages[0]}-{group.ages[1]} años</small></div>
          ))}
        </div>
        <p className="small muted mt-2">Los nombres se generan según la comunidad del club. Al cumplir años cambian de categoría; a los 21 salen de la cantera.</p>
      </Card>

      {data.groups.length ? data.groups.map((group) => (
        <section key={group.category}>
          <div className="section-title"><h2>{group.label}</h2><Badge tone="neutral">{group.players.length}</Badge></div>
          <div className="player-grid">
            {group.players.map((player) => (
              <Card key={player.id}>
                <div className="inline" style={{ alignItems: 'flex-start' }}>
                  <Avatar player={player} size={48} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="inline" style={{ justifyContent: 'space-between' }}><b style={{ fontSize: 12 }}>{player.name}</b><Badge tone="gold">{player.overall.toFixed(1)}</Badge></div>
                    <div className="player-card-tags"><span>{player.subposition}</span><span className="arch">{player.archetype}</span></div>
                    <div className="small muted mt-1">{player.age} años · potencial {player.potential.toFixed(1)} · {player.youth_category}</div>
                    <Progress value={player.potential} tone="blue" />
                  </div>
                </div>
                <div className="actions mt-2">
                  <Button size="sm" variant="primary" icon={ArrowUpCircle} onClick={() => action(player, 'promote')} loading={busy === `promote-${player.id}`}>Promover</Button>
                  <Button size="sm" variant="danger" icon={Trash2} onClick={() => action(player, 'release')} loading={busy === `release-${player.id}`}>Liberar</Button>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )) : <EmptyState title="Cantera vacía" body="No hay juveniles en la academia. La próxima generación llegará al avanzar la temporada." />}
    </>
  )
}
