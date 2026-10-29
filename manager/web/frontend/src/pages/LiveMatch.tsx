import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FastForward, Flag, Play, SkipForward, Timer, UserRoundPlus } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { LivePayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, Crest, Field, LoadingBlock, PageHeader } from '../components/ui'

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

  return (
    <>
      <PageHeader
        eyebrow={`${data.fixture.label} · ${dateLabel(data.fixture.date)}`}
        title="Partido en directo"
        subtitle={`${data.home.name} vs ${data.away.name} · ${data.finished ? 'Finalizado' : `${data.quarter}º cuarto · ${data.minute}'`}`}
        actions={<Badge tone={data.finished ? 'ok' : 'danger'}>{data.finished ? 'Finalizado' : 'EN DIRECTO'}</Badge>}
      />

      <Card>
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
            <h3>Tu once</h3>
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th></th><th>Jugador</th><th>Pos</th><th className="num">Min</th><th className="num">G</th><th className="num">A</th><th className="num">Rating</th><th className="num">Fatiga</th></tr></thead>
                <tbody>{data.player_rows.map((row) => {
                  const player = data.line.find((item) => item.id === row.id)
                  return <tr key={row.id}><td>{player ? <Avatar player={player} size={24} /> : null}</td><td>{row.name}</td><td>{row.position}</td><td className="num">{row.minutes}</td><td className="num">{row.goals}</td><td className="num">{row.assists}</td><td className="num">{row.rating.toFixed(2)}</td><td className="num">{row.fatigue}%</td></tr>
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
