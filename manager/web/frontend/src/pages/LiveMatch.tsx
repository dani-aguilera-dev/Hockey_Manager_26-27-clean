import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FastForward, Flag, MessageSquare, MonitorCheck, Play, Timer, UserRoundPlus, Volume2, VolumeX } from 'lucide-react'
import { api } from '../lib/api'
import { MatchAudio } from '../lib/matchAudio'
import { dateLabel } from '../lib/format'
import type { LivePayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, Crest, Field, LoadingBlock, PageHeader } from '../components/ui'
const MatchViewer3D = lazy(() => import('../components/MatchViewer3D'))

export default function LiveMatch() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<LivePayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [outId, setOutId] = useState('')
  const [inId, setInId] = useState('')
  const [mentality, setMentality] = useState('equilibrada')
  const [press, setPress] = useState('media')
  const [tempo, setTempo] = useState('normal')
  const [passing, setPassing] = useState('mixto')
  const [audioOn, setAudioOn] = useState(() => {
    try { return localStorage.getItem('hm_audio') === '1' } catch { return false }
  })
  const audioRef = useRef<MatchAudio | null>(null)
  const audioPrimed = useRef(false)
  const audioSeen = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (!audioOn) {
      audioRef.current?.disable()
      return
    }
    if (!audioRef.current) audioRef.current = new MatchAudio()
    void audioRef.current.enable()
  }, [audioOn])

  useEffect(() => () => { audioRef.current?.dispose() }, [])

  useEffect(() => {
    if (!data) return
    const keyOf = (event: { minute: number; type: string; text: string }) => `${event.minute}|${event.type}|${event.text}`
    if (!audioPrimed.current) {
      for (const event of data.events) audioSeen.current.add(keyOf(event))
      audioPrimed.current = true
      return
    }
    const fresh = data.events.filter((event) => {
      const key = keyOf(event)
      if (audioSeen.current.has(key)) return false
      audioSeen.current.add(key)
      return true
    })
    if (!audioOn) return
    for (const event of fresh.slice(-6)) audioRef.current?.play(event.type)
  }, [data, audioOn])

  useEffect(() => {
    api.get<LivePayload>('/match/live')
      .then(({ data }) => {
        setData(data)
        setMentality(data.tactics.mentality)
        setPress(data.tactics.press)
        setTempo(data.tactics.tempo)
        setPassing(data.tactics.passing)
        setOutId(data.line[0]?.id || '')
        setInId(data.bench[0]?.id || '')
      })
      .catch((err) => {
        toast(err instanceof Error ? err.message : 'No hay partido en directo.', 'danger')
        navigate('/game/match', { replace: true })
      })
      .finally(() => setLoading(false))
  }, [navigate, toast])

  async function advance(mode: 'quarter' | 'moment' | 'rest') {
    setBusy(mode)
    try {
      const response = await api.post<LivePayload>('/match/live/advance', { mode })
      setData(response.data)
      if (response.data.finished) toast('El partido ha terminado. Revisa el parte.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo avanzar el partido.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function applyTactics() {
    setBusy('tactics')
    try {
      const response = await api.post<LivePayload>('/match/live/tactics', { mentality, press, tempo, passing })
      setData(response.data)
      toast(response.message || 'Táctica actualizada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo cambiar la táctica.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function substitute() {
    setBusy('sub')
    try {
      const response = await api.post<LivePayload>('/match/live/sub', { out_id: outId, in_id: inId })
      setData(response.data)
      toast(response.message || 'Cambio realizado.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo hacer el cambio.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function requestReview() {
    if (!data?.last_decision) return
    setBusy('review')
    try {
      const response = await api.post<LivePayload>('/match/live/review', { decision: data.last_decision.type })
      setData(response.data)
      toast(response.message || 'Revisión completada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo solicitar la revisión.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function protest(tone: 'respetuosa' | 'vehemente') {
    setBusy(`protest-${tone}`)
    try {
      const response = await api.post<LivePayload>('/match/live/protest', { tone })
      setData(response.data)
      toast(response.message || 'Protesta registrada.', tone === 'respetuosa' ? 'info' : 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo protestar.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function finish() {
    setBusy('finish')
    try {
      const response = await api.post<{ state: unknown }>('/match/live/finish')
      applyState(response.data.state as never)
      navigate('/game/report')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo finalizar el partido.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Conectando con el directo…" />
  if (!data) return <Card><p className="muted">No hay partido en directo.</p><Button onClick={() => navigate('/game/match')}>Volver a la previa</Button></Card>

  const homeStats = data.stats.home
  const awayStats = data.stats.away
  const homePossession = Number(homeStats.possession || 0)
  const awayPossession = Number(awayStats.possession || 0)
  const barHome = homePossession || 50
  const decisionLabels: Record<string, string> = { goal: 'Gol', goal_disallowed: 'Gol anulado', penalty_corner: 'Penalty corner', penalty_stroke: 'Penalty stroke' }
  const referralsLeft = data.referrals?.[data.user_side] ?? 0
  const momentum = Number(data.snapshot?.momentum || 0)
  const momentumHome = Math.max(8, Math.min(92, Math.round(50 + momentum * 50)))
  const momentumLabel = momentum > 0.15 ? `${data.home.name} domina` : momentum < -0.15 ? `${data.away.name} domina` : 'Partido igualado'
  const momentumLog = (data.snapshot?.momentum_log || []).slice(-4).reverse()
  const reviewable = data.last_decision && !data.last_decision.reviewed && (
    data.last_decision.side !== data.user_side
    || (data.last_decision.type === 'goal_disallowed' && data.last_decision.side === data.user_side)
  )

  return (
    <>
      <PageHeader
        eyebrow={`${data.fixture.label} · ${dateLabel(data.fixture.date)}`}
        title="Partido en directo"
        subtitle={`${data.home.name} vs ${data.away.name} · ${data.finished ? 'Finalizado' : `${data.quarter}º cuarto · ${data.minute}'`}`}
        actions={
          <div className="inline">
            <Button
              size="sm"
              variant="ghost"
              icon={audioOn ? Volume2 : VolumeX}
              aria-pressed={audioOn}
              title={audioOn ? 'Silenciar ambiente' : 'Activar ambiente del partido'}
              onClick={() => {
                const next = !audioOn
                try { localStorage.setItem('hm_audio', next ? '1' : '0') } catch {}
                setAudioOn(next)
              }}
            >
              {audioOn ? 'Ambiente on' : 'Ambiente off'}
            </Button>
            <Badge tone={data.finished ? 'ok' : 'danger'}>{data.finished ? 'Finalizado' : 'EN DIRECTO'}</Badge>
          </div>
        }
      />

      <Suspense fallback={<div className="match-viewer-3d"><LoadingBlock label="Cargando visor 3D…" /></div>}>
        <MatchViewer3D data={data} />
      </Suspense>

      <Card className="mt-2">
        <div className="scoreboard">
          <div className="score-team"><Crest src={data.home.crest} name={data.home.name} size={58} /><div><h2>{data.home.name}</h2><span className="muted">{homePossession}% posesión</span></div></div>
          <div><div className="score-value">{data.score[0]} - {data.score[1]}</div><div className="score-meta">{data.quarter}º cuarto · {data.minute}'</div></div>
          <div className="score-team right"><div><h2>{data.away.name}</h2><span className="muted">{awayPossession}% posesión</span></div><Crest src={data.away.crest} name={data.away.name} size={58} /></div>
        </div>
        <div className="live-actions">
          {data.finished ? (
            <Button variant="primary" size="lg" icon={Flag} onClick={finish} loading={busy === 'finish'}>Finalizar y ver parte</Button>
          ) : (
            <>
              <Button variant="primary" icon={Play} onClick={() => advance('quarter')} loading={busy === 'quarter'}>Avanzar cuarto</Button>
              <Button icon={Timer} onClick={() => advance('moment')} loading={busy === 'moment'}>Avanzar momento</Button>
              <Button icon={FastForward} onClick={() => advance('rest')} loading={busy === 'rest'}>Simular resto</Button>
            </>
          )}
        </div>
      </Card>

      <div className="live-grid mt-2">
        <div className="stack">
          <Card>
            <h3>Estadísticas</h3>
            <div className="possession-bar"><span style={{ width: `${barHome}%` }} /><span style={{ width: `${100 - barHome}%` }} /></div>
            {[
              ['Posesión', `${homePossession}%`, `${awayPossession}%`],
              ['Tiros', homeStats.shots || 0, awayStats.shots || 0],
              ['A puerta', homeStats.shots_on_target || 0, awayStats.shots_on_target || 0],
              ['Penaltis córner', homeStats.pc || 0, awayStats.pc || 0],
              ['Paradas', homeStats.saves || 0, awayStats.saves || 0],
              ['Tarjetas V/A/R', `${homeStats.green || 0}/${homeStats.yellow || 0}/${homeStats.red || 0}`, `${awayStats.green || 0}/${awayStats.yellow || 0}/${awayStats.red || 0}`],
            ].map(([label, home, away]) => (
              <div className="stat-line" key={label}><b>{home}</b><span>{label}</span><b className="num">{away}</b></div>
            ))}
          </Card>
          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0 }}>Momentum</h3>
              <Badge tone={Math.abs(momentum) > 0.15 ? 'gold' : 'neutral'}>{momentumLabel}</Badge>
            </div>
            <div className="momentum-bar mt-2" role="img" aria-label={`Momentum ${Math.round(momentum * 100)} a favor de ${momentum >= 0 ? data.home.name : data.away.name}`}>
              <span className="momentum-home" style={{ width: `${momentumHome}%` }} />
              <span className="momentum-away" style={{ width: `${100 - momentumHome}%` }} />
            </div>
            <div className="momentum-labels"><span>{data.home.name}</span><b>{momentum > 0 ? '+' : ''}{Math.round(momentum * 100)}</b><span>{data.away.name}</span></div>
            {momentumLog.length > 0 && (
              <div className="stack-sm mt-2">
                {momentumLog.map((item, index) => (
                  <div className="momentum-row" key={`${item.minute}-${index}`}>
                    <span className="event-minute">{item.minute}'</span>
                    <p className="small">{item.reason || 'Cambio de ritmo'} · <b>{item.momentum > 0 ? data.home.name : data.away.name}</b></p>
                  </div>
                ))}
              </div>
            )}
          </Card>
          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0 }}>Revisión de vídeo</h3>
              <Badge tone={referralsLeft ? 'neutral' : 'danger'}>{referralsLeft} referencia(s)</Badge>
            </div>
            {reviewable ? (
              <>
                <p className="small muted mt-1">
                  Última decisión revisable: <b>{decisionLabels[data.last_decision!.type] || data.last_decision!.type}</b> ({data.last_decision!.team_name}, {data.last_decision!.minute}'). El capitán puede pedir revisión.
                </p>
                <Button size="sm" icon={MonitorCheck} onClick={requestReview} loading={busy === 'review'} disabled={!referralsLeft}>Solicitar revisión</Button>
              </>
            ) : (
              <p className="small muted mt-1">No hay una decisión revisable contra tu equipo. Avanza el partido para generar una jugada.</p>
            )}
            {data.reviews.length > 0 && (
              <div className="stack-sm mt-2">
                {data.reviews.slice().reverse().slice(0, 3).map((review, index) => (
                  <div className={`review-row ${review.overturned ? 'overturned' : 'upheld'}`} key={`${review.minute}-${index}`}>
                    <Badge tone={review.overturned ? 'ok' : 'danger'}>{review.overturned ? 'Corregida' : 'Mantenida'}</Badge>
                    <p className="small">{review.text}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0 }}>Protesta arbitral</h3>
              <Badge tone={data.protest_available ? 'gold' : 'neutral'} className={data.protest_available ? '' : 'protest-used'}>{data.protest_available ? 'Disponible' : 'Usada'}</Badge>
            </div>
            <p className="small muted mt-1">Puedes protestar una decisión por partido. La protesta respetuosa recibe un aviso; la vehemente puede acarrear tarjeta.</p>
            <div className="actions">
              <Button size="sm" icon={MessageSquare} onClick={() => protest('respetuosa')} loading={busy === 'protest-respetuosa'} disabled={!data.protest_available} data-testid="live-protest-respectful">Respetuosa</Button>
              <Button size="sm" variant="danger" icon={MessageSquare} onClick={() => protest('vehemente')} loading={busy === 'protest-vehemente'} disabled={!data.protest_available} data-testid="live-protest-vehement">Vehemente</Button>
            </div>
          </Card>
          <Card>
            <h3>Tu once</h3>
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th></th><th>Jugador</th><th>Pos</th><th className="num">Min</th><th className="num">G</th><th className="num">A</th><th className="num" title="Decisiones">Dec</th><th className="num" title="Pases clave">PC+</th><th className="num" title="Pérdidas">Per</th><th className="num">Rating</th><th className="num">Fatiga</th></tr></thead>
                <tbody>{data.player_rows.map((row) => {
                  const player = data.line.find((item) => item.id === row.id)
                  return <tr key={row.id}><td>{player ? <Avatar player={player} size={24} /> : null}</td><td>{row.name}</td><td>{row.position}</td><td className="num">{row.minutes}</td><td className="num">{row.goals}</td><td className="num">{row.assists}</td><td className="num">{row.decisions ?? 0}</td><td className="num">{row.key_passes ?? 0}</td><td className="num">{row.turnovers ?? 0}</td><td className="num">{row.rating.toFixed(2)}</td><td className="num">{row.fatigue}%</td></tr>
                })}</tbody>
              </table>
            </div>
          </Card>
        </div>
        <div className="live-side">
          <Card>
            <h3>Crónica en vivo</h3>
            <div className="event-list">
              {data.events.length ? data.events.slice().reverse().map((event, index) => (
                <div className={`event-row ${event.type}`} key={`${event.minute}-${index}`}><span className="event-minute">{event.minute}'</span><p><b>{event.text}</b>{event.score && <span className="muted"> · {event.score}</span>}</p></div>
              )) : <p className="small muted">El partido está a punto de comenzar. Avanza un cuarto o un momento para ver la primera acción.</p>}
            </div>
          </Card>
          {!data.finished && (
            <>
              <Card>
                <h3>Táctica en directo</h3>
                <div className="form-grid" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
                  <Field label="Mentalidad"><select value={mentality} onChange={(event) => setMentality(event.target.value)}>{['muy_defensiva', 'defensiva', 'equilibrada', 'ofensiva', 'muy_ofensiva'].map((value) => <option key={value} value={value}>{value.replaceAll('_', ' ')}</option>)}</select></Field>
                  <Field label="Presión"><select value={press} onChange={(event) => setPress(event.target.value)}>{['baja', 'media', 'alta', 'muy_alta'].map((value) => <option key={value} value={value}>{value}</option>)}</select></Field>
                  <Field label="Tempo"><select value={tempo} onChange={(event) => setTempo(event.target.value)}>{['lento', 'normal', 'rapido'].map((value) => <option key={value} value={value}>{value}</option>)}</select></Field>
                  <Field label="Pase"><select value={passing} onChange={(event) => setPassing(event.target.value)}>{['corto', 'mixto', 'directo'].map((value) => <option key={value} value={value}>{value}</option>)}</select></Field>
                </div>
                <Button size="sm" className="mt-2" onClick={applyTactics} loading={busy === 'tactics'}>Aplicar táctica</Button>
              </Card>
              <Card>
                <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Cambios</h3><Badge tone={data.subs_left ? 'neutral' : 'danger'}>{data.subs_left} restantes</Badge></div>
                <div className="stack-sm mt-2">
                  <Field label="Sale"><select value={outId} onChange={(event) => setOutId(event.target.value)}>{data.line.map((player) => <option key={player.id} value={player.id}>{player.name} · fatiga {player.fatigue.toFixed(0)}%</option>)}</select></Field>
                  <Field label="Entra"><select value={inId} onChange={(event) => setInId(event.target.value)}>{data.bench.map((player) => <option key={player.id} value={player.id}>{player.name} · OVR {player.overall.toFixed(1)}</option>)}</select></Field>
                  <Button size="sm" icon={UserRoundPlus} onClick={substitute} loading={busy === 'sub'} disabled={!data.subs_left}>Hacer cambio</Button>
                </div>
              </Card>
            </>
          )}
        </div>
      </div>
    </>
  )
}
