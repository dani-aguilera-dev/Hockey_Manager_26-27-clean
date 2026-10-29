import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Flag, Play, Zap } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { MatchPreviewPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, Crest, LoadingBlock, PageHeader } from '../components/ui'
import { Pitch } from '../components/Pitch'

export default function MatchPreview() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<MatchPreviewPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [travel, setTravel] = useState('equilibrado')
  const [busy, setBusy] = useState<string | null>(null)

  useEffect(() => {
    api.get<MatchPreviewPayload>('/match')
      .then(({ data }) => {
        if (data.live) {
          navigate('/game/live', { replace: true })
          return
        }
        setData(data)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la previa.', 'danger'))
      .finally(() => setLoading(false))
  }, [navigate, toast])

  async function quick() {
    setBusy('quick')
    try {
      const response = await api.post<{ state: unknown; report: unknown }>('/match/quick', { travel })
      applyState(response.data.state as never)
      toast(response.message || 'Partido simulado.', 'success')
      navigate('/game/report')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo simular el partido.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function live() {
    setBusy('live')
    try {
      await api.post('/match/live/start', { travel })
      navigate('/game/live')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo iniciar el directo.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Preparando la previa…" />
  if (!data || !data.fixture || !data.home || !data.away) return <Card><p className="muted">No hay partido pendiente.</p><Button onClick={() => navigate('/game')}>Volver al club</Button></Card>

  const { fixture, home, away } = data

  return (
    <>
      <PageHeader
        eyebrow={`${fixture.label} · ${dateLabel(fixture.date)}`}
        title="La previa"
        subtitle={`${home.name} vs ${away.name} · ${home.stadium_name}`}
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button>}
      />

      <Card>
        <div className="scoreboard">
          <div className="score-team"><Crest src={home.crest} name={home.name} size={64} /><div><h2>{home.name}</h2><span className="muted">{home.position || '—'}º · {home.points} pts · moral {home.morale}/20</span></div></div>
          <div><div className="score-value">VS</div><div className="score-meta">{dateLabel(fixture.date)}</div></div>
          <div className="score-team right"><div><h2>{away.name}</h2><span className="muted">{away.position || '—'}º · {away.points} pts · moral {away.morale}/20</span></div><Crest src={away.crest} name={away.name} size={64} /></div>
        </div>
        <div className="match-strip"><Badge tone={fixture.is_cup ? 'gold' : 'blue'}>{fixture.label}</Badge><span>{home.stadium_name}</span><span>·</span><span>Aforo {home.stadium_capacity}</span>{fixture.is_cup && <Badge tone="warn">Eliminatoria a partido único</Badge>}</div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <h3>Claves del partido</h3>
          <div className="stack-sm">
            <div><span className="small muted">Forma</span><p className="small">{home.name}: {data.home_form} · {away.name}: {data.away_form}</p></div>
            <div><span className="small muted">Peligro</span><p className="small">{data.home_top ? `${data.home_top.name} (${data.home_top.season_goals} goles)` : '—'} · {data.away_top ? `${data.away_top.name} (${data.away_top.season_goals} goles)` : '—'}</p></div>
            <div><span className="small muted">Bajas</span><p className="small">{home.name}: {data.home_absences?.length ? data.home_absences.map((player) => player.name).join(', ') : 'sin bajas'}<br />{away.name}: {data.away_absences?.length ? data.away_absences.map((player) => player.name).join(', ') : 'sin bajas'}</p></div>
          </div>
        </Card>
        <Card>
          <h3>Jugar</h3>
          {data.travel?.length ? (
            <div className="stack-sm">
              <span className="small muted">Viaje</span>
              {data.travel.map((option) => (
                <label className={`option-card ${travel === option.id ? 'selected' : ''}`} key={option.id}>
                  <input type="radio" checked={travel === option.id} onChange={() => setTravel(option.id)} />
                  <span><b>{option.label}</b><br /><span>{money(option.cost)} · fatiga +{Math.round(option.fatigue * 100)}% · {option.notes}</span></span>
                </label>
              ))}
            </div>
          ) : <p className="small muted">Juegas en casa. No hay desplazamiento.</p>}
          <div className="actions mt-2">
            <Button variant="primary" icon={Zap} onClick={quick} loading={busy === 'quick'}>Simulación rápida</Button>
            {!fixture.is_cup && <Button variant="blue" icon={Play} onClick={live} loading={busy === 'live'}>Jugar en directo</Button>}
          </div>
          {fixture.is_cup && <p className="small muted mt-1">La Copa se juega por ahora en simulación rápida.</p>}
          <p className="small muted mt-1">Si no has planificado la semana, el segundo entrenador aplicará el plan automático.</p>
        </Card>
      </div>

      {data.press_context && (
        <Card className="mt-2">
          <div className="cat">LA PREVIA DEL RIVAL</div>
          <h3 style={{ margin: '4px 0' }}>{data.press_context.coach}</h3>
          <p className="press-quote">«{data.press_context.quote}»</p>
          <Button size="sm" className="mt-1" onClick={() => navigate('/game/press')}>Ir a la rueda de prensa</Button>
        </Card>
      )}

      <Card className="mt-2" padded={false}>
        <div style={{ padding: '18px 18px 0' }}><div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">ONCE INICIAL</div><h3 style={{ margin: '3px 0 0' }}>Tu equipo</h3></div><Button size="sm" onClick={() => navigate('/game/tactics')}>Editar once</Button></div></div>
        <Pitch rows={data.slot_rows || []} />
      </Card>

      <Card className="mt-2">
        <h3>Banquillo</h3>
        <div className="player-grid">
          {data.bench?.map((player) => <div className="player-card" key={player.id}><Avatar player={player} size={36} /><div className="player-card-body"><span className="player-card-name">{player.name}</span><span className="player-card-sub">{player.subposition} · OVR {player.overall.toFixed(1)} · fatiga {player.fatigue.toFixed(0)}%</span></div></div>)}
        </div>
      </Card>
    </>
  )
}
