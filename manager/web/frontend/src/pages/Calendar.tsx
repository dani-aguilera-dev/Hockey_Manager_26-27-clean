import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CalendarDays, Check, ChevronLeft, ChevronRight, Clock3, Play, Plus, Trash2, X } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { CalendarPayload, FriendlyItem } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Crest, Field, LoadingBlock, PageHeader, StatCard } from '../components/ui'

export default function CalendarPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<CalendarPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [opponent, setOpponent] = useState('')
  const [day, setDay] = useState('')
  const [home, setHome] = useState(true)
  const [notes, setNotes] = useState('')
  const [monthCursor, setMonthCursor] = useState('')

  function load() {
    setLoading(true)
    api.get<CalendarPayload>('/calendar')
      .then(({ data }) => {
        setData(data)
        if (!monthCursor) setMonthCursor(data.today.slice(0, 7))
        if (!opponent && data.friendlies.candidates[0]) setOpponent(data.friendlies.candidates[0].id)
        if (!day && data.friendlies.dates[0]) setDay(data.friendlies.dates[0])
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el calendario.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function createFriendly() {
    if (!opponent || !day) return
    setBusy('create')
    try {
      const response = await api.post<{ state: unknown }>('/friendlies', { opponent_id: opponent, date: day, home, notes })
      applyState(response.data.state as never)
      toast(response.message || 'Amistoso programado.', 'success')
      setNotes('')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo programar el amistoso.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function playFriendly(item: FriendlyItem) {
    setBusy(`play-${item.id}`)
    try {
      const response = await api.post<{ state: unknown }>(`/friendlies/${item.id}/play`)
      applyState(response.data.state as never)
      toast(response.message || 'Amistoso disputado.', 'success')
      navigate('/game/report')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo jugar el amistoso.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function cancelFriendly(item: FriendlyItem) {
    setBusy(`cancel-${item.id}`)
    try {
      const response = await api.delete<{ state: unknown }>(`/friendlies/${item.id}`)
      applyState(response.data.state as never)
      toast(response.message || 'Amistoso cancelado.', 'success')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo cancelar el amistoso.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Cargando calendario y amistosos…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el calendario.</p></Card>

  const pending = data.friendlies.items.filter((item) => !item.played)
  const played = data.friendlies.items.filter((item) => item.played)
  const upcoming = data.fixtures.filter((fixture) => !fixture.played).slice(0, 8)
  const cursor = monthCursor || data.today.slice(0, 7)
  const cursorDate = new Date(`${cursor}-01T00:00:00`)
  const monthLabel = cursorDate.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })
  const monthTitle = monthLabel.charAt(0).toUpperCase() + monthLabel.slice(1)
  const firstWeekday = (cursorDate.getDay() + 6) % 7
  const daysInMonth = new Date(cursorDate.getFullYear(), cursorDate.getMonth() + 1, 0).getDate()
  const officialByDate = new Map<string, typeof data.fixtures>()
  data.fixtures.forEach((fixture) => officialByDate.set(fixture.date, [...(officialByDate.get(fixture.date) || []), fixture]))
  const friendlyByDate = new Map<string, typeof data.friendlies.items>()
  data.friendlies.items.forEach((item) => friendlyByDate.set(item.date, [...(friendlyByDate.get(item.date) || []), item]))
  const monthCells = Array.from({ length: 42 }, (_, index) => {
    const dayNumber = index - firstWeekday + 1
    if (dayNumber < 1 || dayNumber > daysInMonth) return null
    const day = `${cursor}-${String(dayNumber).padStart(2, '0')}`
    return { day, dayNumber, official: officialByDate.get(day) || [], friendlies: friendlyByDate.get(day) || [] }
  })
  function moveMonth(delta: number) {
    const next = new Date(cursorDate.getFullYear(), cursorDate.getMonth() + delta, 1)
    setMonthCursor(`${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}`)
  }

  return (
    <>
      <PageHeader
        eyebrow={`${data.competition.short_name} · ${data.season}`}
        title="Calendario y amistosos"
        subtitle="Planifica la temporada, concierta partidos de preparación y llega a cada jornada con el once listo."
        actions={<><Button icon={CalendarDays} onClick={load}>Actualizar</Button><Button variant="primary" icon={Plus} onClick={() => document.getElementById('friendly-form')?.scrollIntoView({ behavior: 'smooth' })}>Concertar amistoso</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Hoy" value={dateLabel(data.today)} hint={data.competition.name} tone="gold" />
        <StatCard label="Amistosos" value={`${data.friendlies.pending} pendientes`} hint={`${data.friendlies.played} jugados`} tone="blue" />
        <StatCard label="Próximo oficial" value={data.next_fixture ? dateLabel(data.next_fixture.date) : '—'} hint={data.next_fixture ? `${data.next_fixture.home_name} vs ${data.next_fixture.away_name}` : 'Sin partido'} />
        <StatCard label="Fechas libres" value={data.friendlies.dates.length} hint="Próximos 75 días" />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">VISTA MENSUAL</div><h3 style={{ margin: '3px 0 0' }}>{monthTitle}</h3></div>
          <div className="inline"><Button size="sm" icon={ChevronLeft} onClick={() => moveMonth(-1)} aria-label="Mes anterior" /><Button size="sm" icon={ChevronRight} onClick={() => moveMonth(1)} aria-label="Mes siguiente" /></div>
        </div>
        <div className="month-grid mt-2">
          {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].map((label) => <div className="month-weekday" key={label}>{label}</div>)}
          {monthCells.map((cell, index) => cell ? (
            <div className={`month-day ${cell.day === data.today ? 'today' : ''}`} key={cell.day}>
              <span className="month-day-number">{cell.dayNumber}</span>
              {cell.official.slice(0, 2).map((fixture) => <button type="button" className="month-event official" key={fixture.id} onClick={() => navigate('/game/match')} title={`${fixture.home_name} vs ${fixture.away_name}`}>{fixture.home_name} · {fixture.away_name}</button>)}
              {cell.friendlies.slice(0, 2).map((item) => <button type="button" className="month-event friendly" key={item.id} onClick={() => navigate('/game/calendar')} title={`Amistoso · ${item.home_name} vs ${item.away_name}`}>Amistoso · {item.home_name}</button>)}
            </div>
          ) : <div className="month-day empty" key={`empty-${index}`} />)}
        </div>
        <div className="inline mt-2"><Badge tone="blue">Oficial</Badge><Badge tone="gold">Amistoso</Badge><span className="small muted">Haz clic en un partido para prepararlo.</span></div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">PRÓXIMOS PARTIDOS OFICIALES</div><h3 style={{ margin: '3px 0 0' }}>Competición</h3></div><Badge tone="neutral">{upcoming.length}</Badge></div>
          <div className="stack-sm mt-2">
            {upcoming.map((fixture) => (
              <div className="calendar-row" key={fixture.id}>
                <div className="calendar-date"><b>{dateLabel(fixture.date)}</b><span>J{fixture.round} · {fixture.phase}</span></div>
                <div className="calendar-match"><Crest src={fixture.home_crest} name={fixture.home_name} size={24} /><b>{fixture.home_name}</b><span>vs</span><b>{fixture.away_name}</b><Crest src={fixture.away_crest} name={fixture.away_name} size={24} /></div>
                <Button size="sm" variant="ghost" onClick={() => navigate('/game/match')}>Preparar</Button>
              </div>
            ))}
            {!upcoming.length && <p className="small muted">No quedan partidos oficiales en el calendario activo.</p>}
          </div>
        </Card>

        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">AMISTOSOS</div><h3 style={{ margin: '3px 0 0' }}>{pending.length ? 'Pendientes' : 'Sin amistosos pendientes'}</h3></div><Badge tone={pending.length ? 'gold' : 'neutral'}>{pending.length}</Badge></div>
          <div className="stack-sm mt-2">
            {pending.map((item) => (
              <div className="friendly-row" key={item.id}>
                <div><b>{item.home_name} vs {item.away_name}</b><span>{dateLabel(item.date)} · {item.is_home ? 'Casa' : 'Fuera'}{item.notes ? ` · ${item.notes}` : ''}</span></div>
                <div className="inline">
                  <Button size="sm" variant="primary" icon={Play} onClick={() => playFriendly(item)} loading={busy === `play-${item.id}`} disabled={item.date > data.today}>{item.date > data.today ? 'Esperando fecha' : 'Jugar'}</Button>
                  <Button size="sm" variant="ghost" icon={Trash2} onClick={() => cancelFriendly(item)} loading={busy === `cancel-${item.id}`}>Cancelar</Button>
                </div>
              </div>
            ))}
            {!pending.length && <p className="small muted">Usa el formulario para añadir un amistoso de preparación.</p>}
          </div>
          {played.length > 0 && (
            <div className="mt-2">
              <div className="cat">RESULTADOS</div>
              {played.slice().reverse().map((item) => (
                <div className="calendar-row" key={item.id}>
                  <div className="calendar-date"><b>{dateLabel(item.date)}</b><span>Amistoso</span></div>
                  <div className="calendar-match"><b>{item.home_name}</b><span>{item.home_goals} - {item.away_goals}</span><b>{item.away_name}</b></div>
                  <Badge tone="ok"><Check size={12} /> Jugado</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div id="friendly-form">
      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">NUEVO AMISTOSO</div><h3 style={{ margin: '3px 0 0' }}>Concertar partido de preparación</h3></div><Badge tone="blue"><Clock3 size={12} /> Sin puntos</Badge></div>
        <p className="small muted mt-1">Elige un rival, una fecha libre y si juegas en casa o fuera. No cuenta para la clasificación; sirve para probar el once y dar minutos.</p>
        <div className="form-row mt-2">
          <Field label="Rival">
            <select value={opponent} onChange={(event) => setOpponent(event.target.value)}>
              {data.friendlies.candidates.map((candidate) => <option key={candidate.id} value={candidate.id}>{candidate.name} · {candidate.league_name} · {candidate.city}</option>)}
            </select>
          </Field>
          <Field label="Fecha">
            <select value={day} onChange={(event) => setDay(event.target.value)}>
              {data.friendlies.dates.slice(0, 60).map((date) => <option key={date} value={date}>{dateLabel(date)}</option>)}
            </select>
          </Field>
          <Field label="Condición">
            <select value={home ? '1' : '0'} onChange={(event) => setHome(event.target.value === '1')}>
              <option value="1">En casa</option>
              <option value="0">A domicilio</option>
            </select>
          </Field>
          <Field label="Nota"><input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Ej. probar el 3-4-3" /></Field>
        </div>
        <div className="actions mt-2"><Button variant="primary" icon={Plus} onClick={createFriendly} loading={busy === 'create'} disabled={!opponent || !day}>Programar amistoso</Button><Button icon={X} onClick={() => { setNotes(''); }}>Limpiar nota</Button></div>
      </Card>
      </div>
    </>
  )
}
