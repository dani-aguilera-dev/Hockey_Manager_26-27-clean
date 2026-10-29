import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Activity, HeartPulse, ShieldAlert, Stethoscope, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { Player } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

interface MedicalHistoryItem {
  kind: 'injury' | 'card'
  player_id: string
  player_name: string
  date?: string
  type?: string
  severity?: string
  matches?: number
  label?: string
  reason?: string
  minute?: number
  duration_minutes?: number
}

interface MedicalPayload {
  injuries: Player[]
  suspensions: Player[]
  history: MedicalHistoryItem[]
  summary: {
    available: number
    injured: number
    suspended: number
    avg_fatigue: number
    risk: number
    physio: number
    fitness_coach: number
  }
}

export default function MedicalPage() {
  const navigate = useNavigate()
  const { game } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<MedicalPayload | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<MedicalPayload>('/medical')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la enfermería.', 'danger'))
      .finally(() => setLoading(false))
  }, [toast])

  if (loading) return <LoadingBlock label="Cargando parte médico…" />
  if (!data || !game) return <Card><p className="muted">No se pudo cargar la enfermería.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow={`${game.competition.short_name} · ${game.game.season}`}
        title="Enfermería"
        subtitle="Lesiones, sanciones, carga física y disponibilidad real de la plantilla."
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game/squad')}>Volver a plantilla</Button>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Disponibles" value={`${data.summary.available}/${game.team.players.length}`} hint={`${data.summary.injured} lesionados · ${data.summary.suspended} sancionados`} tone={data.summary.injured || data.summary.suspended ? 'danger' : 'ok'} icon={Users} />
        <StatCard label="Fatiga media" value={`${data.summary.avg_fatigue}%`} hint={`${data.summary.risk} jugador(es) en zona de riesgo`} tone={data.summary.risk ? 'danger' : 'ok'} icon={Activity} />
        <StatCard label="Fisioterapeuta" value={`${data.summary.physio}/100`} hint="Recuperación y prevención" icon={Stethoscope} />
        <StatCard label="Preparador físico" value={`${data.summary.fitness_coach}/100`} hint="Carga y resistencia" icon={HeartPulse} />
      </div>

      <div className="split-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>Lesionados</h3>
            <Badge tone={data.injuries.length ? 'danger' : 'ok'}>{data.injuries.length ? `${data.injuries.length} baja(s)` : 'Sin lesiones'}</Badge>
          </div>
          {data.injuries.length ? (
            <div className="stack-sm mt-2">
              {data.injuries.map((player) => (
                <button type="button" className="squad-status-row" key={player.id} onClick={() => navigate(`/game/player/${player.id}`)} style={{ background: 'none', border: 0, color: 'inherit', textAlign: 'left', width: '100%' }}>
                  <Avatar player={player} size={32} />
                  <span className="squad-status-main">
                    <b>{player.name}</b>
                    <span>{player.subposition} · {player.injury_type || 'Lesión'} · {player.injury_severity || 'leve'}</span>
                  </span>
                  <Badge tone="danger">{player.injury} partido(s)</Badge>
                </button>
              ))}
            </div>
          ) : <p className="small muted mt-2">No hay lesiones activas. El grupo está disponible.</p>}
        </Card>

        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>Sancionados</h3>
            <Badge tone={data.suspensions.length ? 'warn' : 'ok'}>{data.suspensions.length ? `${data.suspensions.length} sanción(es)` : 'Sin sanciones'}</Badge>
          </div>
          {data.suspensions.length ? (
            <div className="stack-sm mt-2">
              {data.suspensions.map((player) => (
                <button type="button" className="squad-status-row" key={player.id} onClick={() => navigate(`/game/player/${player.id}`)} style={{ background: 'none', border: 0, color: 'inherit', textAlign: 'left', width: '100%' }}>
                  <Avatar player={player} size={32} />
                  <span className="squad-status-main">
                    <b>{player.name}</b>
                    <span>{player.suspension_reason || 'Sanción disciplinaria'}</span>
                  </span>
                  <Badge tone="warn">{player.suspension} partido(s)</Badge>
                </button>
              ))}
            </div>
          ) : <p className="small muted mt-2">No hay sanciones activas.</p>}
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0 }}>Riesgo de carga</h3>
          <Badge tone={data.summary.risk ? 'warn' : 'ok'}>{data.summary.risk ? `${data.summary.risk} en riesgo` : 'Carga controlada'}</Badge>
        </div>
        <div className="stack-sm mt-2">
          {[...game.team.players].sort((a, b) => b.fatigue - a.fatigue).slice(0, 8).map((player) => (
            <div key={player.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <span className="small">{player.name}</span>
                <b className="small">{player.fatigue.toFixed(0)}%</b>
              </div>
              <Progress value={player.fatigue} tone={player.fatigue >= 65 ? 'danger' : player.fatigue >= 40 ? 'gold' : 'ok'} />
            </div>
          ))}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0 }}>Historial médico y disciplinario</h3>
          <Badge tone="neutral">{data.history.length} registro(s)</Badge>
        </div>
        {data.history.length ? (
          <div className="stack-sm mt-2">
            {data.history.map((item, index) => (
              <div className="squad-status-row" key={`${item.player_id}-${item.date}-${index}`}>
                <ShieldAlert size={16} className={item.kind === 'injury' ? 'danger' : 'warn'} />
                <span className="squad-status-main">
                  <b>{item.player_name}</b>
                  <span>
                    {item.kind === 'injury'
                      ? `${item.type || 'Lesión'} · ${item.severity || 'leve'} · ${item.matches || '—'} partido(s)`
                      : `${item.label || item.type || 'Tarjeta'} · ${item.reason || 'sanción'}${item.minute != null ? ` · ${item.minute}′` : ''}`}
                  </span>
                </span>
                <span className="small muted">{item.date ? dateLabel(item.date) : '—'}</span>
              </div>
            ))}
          </div>
        ) : <p className="small muted mt-2">Todavía no hay registros médicos ni disciplinarios.</p>}
      </Card>
    </>
  )
}
