import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, Search, Star, Trash2, UserPlus } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { ShortlistCandidate, ShortlistData, ShortlistEntry } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, StatCard } from '../components/ui'

type Draft = { priority: string; note: string }
type Filter = 'all' | 'alta' | 'media' | 'baja'

const priorityTones: Record<string, 'ok' | 'gold' | 'neutral'> = {
  alta: 'ok',
  media: 'gold',
  baja: 'neutral',
}

export default function ShortlistPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<ShortlistData | null>(null)
  const [candidates, setCandidates] = useState<ShortlistCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [query, setQuery] = useState('')
  const [drafts, setDrafts] = useState<Record<string, Draft>>({})
  const [saved, setSaved] = useState(false)

  function load(search = '') {
    setLoading(true)
    Promise.all([
      api.get<ShortlistData>('/shortlist'),
      api.get<{ candidates: ShortlistCandidate[] }>(`/shortlist/candidates?q=${encodeURIComponent(search)}`),
    ])
      .then(([shortlist, options]) => {
        setData(shortlist.data)
        setCandidates(options.data.candidates)
        setDrafts(Object.fromEntries(shortlist.data.entries.map((entry) => [entry.id, {
          priority: entry.priority,
          note: entry.note,
        }])))
        setSaved(false)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el seguimiento.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function add(candidate: ShortlistCandidate) {
    setBusy(`add-${candidate.id}`)
    try {
      const response = await api.post<{ shortlist: ShortlistData; state: unknown }>('/shortlist', {
        player_id: candidate.id,
        priority: 'media',
        note: '',
      })
      setData(response.data.shortlist)
      applyState(response.data.state as never)
      setCandidates((current) => current.filter((item) => item.id !== candidate.id))
      setSaved(true)
      toast(response.message || 'Jugador añadido.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo añadir al seguimiento.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function save(entry: ShortlistEntry) {
    const draft = drafts[entry.id]
    if (!draft) return
    setBusy(`save-${entry.id}`)
    try {
      const response = await api.post<{ shortlist: ShortlistData; state: unknown }>(`/shortlist/${entry.id}`, draft)
      setData(response.data.shortlist)
      applyState(response.data.state as never)
      setSaved(true)
      toast(response.message || 'Seguimiento actualizado.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo actualizar el seguimiento.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function remove(entry: ShortlistEntry) {
    setBusy(`remove-${entry.id}`)
    try {
      const response = await api.delete<{ shortlist: ShortlistData; state: unknown }>(`/shortlist/${entry.id}`)
      setData(response.data.shortlist)
      applyState(response.data.state as never)
      toast(response.message || 'Jugador retirado.', 'info')
      await load(query)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo retirar del seguimiento.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Revisando la lista de seguimiento…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el seguimiento.</p></Card>

  const rows = filter === 'all' ? data.entries : data.entries.filter((entry) => entry.priority === filter)
  return (
    <>
      <PageHeader
        eyebrow="Mercado · seguimiento · objetivos"
        title="Lista de seguimiento"
        subtitle="Guarda objetivos de fichaje, prioriza y anota por qué te interesan. El seguimiento refleja el club, valor y contrato actuales."
        actions={<>{saved && <Badge tone="ok" className="shortlist-saved">Guardado</Badge>}<Button icon={Star} onClick={() => load(query)}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Objetivos" value={data.summary.total} hint={`${data.summary.available} disponibles`} tone="blue" icon={Star} />
        <StatCard label="Prioridad alta" value={data.summary.high} hint={`${data.summary.medium} media · ${data.summary.low} baja`} tone="gold" icon={Eye} />
        <StatCard label="Valor total" value={money(data.summary.total_value)} hint="Valor de mercado sumado" />
        <StatCard label="Contratos que expiran" value={data.summary.expiring} hint="Este curso o antes" tone={data.summary.expiring ? 'danger' : 'ok'} />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">AÑADIR OBJETIVO</div><h3 style={{ margin: '3px 0 0' }}>Buscar en el mercado</h3></div>
          <UserPlus size={20} className="gold" />
        </div>
        <div className="shortlist-search mt-2">
          <Field label="Jugador o club"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nombre o club…" onKeyDown={(event) => { if (event.key === 'Enter') load(query) }} /></Field>
          <Button icon={Search} onClick={() => load(query)} loading={loading}>Buscar</Button>
        </div>
        <div className="shortlist-candidates mt-2">
          {candidates.map((candidate) => (
            <div className="shortlist-candidate" key={candidate.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><Badge tone="neutral">{candidate.league_name}</Badge><b className="gold">{candidate.overall}</b></div>
              <b>{candidate.name}</b>
              <span className="small muted">{candidate.team_name} · {candidate.position} · {candidate.age} años</span>
              <span className="small muted">Valor {money(candidate.value)} · petición {money(candidate.asking)}</span>
              <Button size="sm" variant="primary" icon={Star} onClick={() => add(candidate)} loading={busy === `add-${candidate.id}`} data-testid={`shortlist-add-${candidate.id}`}>Seguir</Button>
            </div>
          ))}
          {!candidates.length && <p className="small muted">No hay candidatos que encajen con la búsqueda.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">OBJETIVOS GUARDADOS</div><h3 style={{ margin: '3px 0 0' }}>Seguimiento activo</h3></div>
          <div className="actions">
            {(['all', 'alta', 'media', 'baja'] as Filter[]).map((value) => <Button key={value} size="sm" variant={filter === value ? 'primary' : 'ghost'} onClick={() => setFilter(value)}>{value === 'all' ? 'Todos' : value}</Button>)}
          </div>
        </div>
        <div className="stack-sm mt-2">
          {rows.map((entry) => {
            const draft = drafts[entry.id] || { priority: entry.priority, note: entry.note }
            return (
              <div className="shortlist-row" key={entry.id}>
                <div className="shortlist-main">
                  <div className="inline"><b>{entry.name}</b><Badge tone={priorityTones[entry.priority]}>{entry.priority_label}</Badge>{entry.transfer_listed && <Badge tone="blue">En venta</Badge>}</div>
                  <span>{entry.team_name} · {entry.league_name} · {entry.position} · {entry.age} años · OVR {entry.overall} / POT {entry.potential}</span>
                  <span>Valor {money(entry.value)} · petición {money(entry.asking)} · contrato {entry.contract_until} · añadido {dateLabel(entry.added)}</span>
                  <div className="shortlist-edit">
                    <Field label="Prioridad">
                      <select value={draft.priority} onChange={(event) => setDrafts({ ...drafts, [entry.id]: { ...draft, priority: event.target.value } })} data-testid={`shortlist-priority-${entry.id}`}>
                        {data.priorities.map((priority) => <option key={priority.id} value={priority.id}>{priority.label}</option>)}
                      </select>
                    </Field>
                    <Field label="Nota">
                      <input value={draft.note} onChange={(event) => setDrafts({ ...drafts, [entry.id]: { ...draft, note: event.target.value } })} placeholder="Motivo del seguimiento…" data-testid={`shortlist-note-${entry.id}`} />
                    </Field>
                  </div>
                </div>
                <div className="shortlist-actions">
                  <Button size="sm" variant="primary" icon={Star} onClick={() => save(entry)} loading={busy === `save-${entry.id}`} data-testid={`shortlist-save-${entry.id}`}>Guardar</Button>
                  <Button size="sm" variant="ghost" icon={Eye} onClick={() => navigate(`/game/market/player/${entry.id}`)}>Abrir</Button>
                  <Button size="sm" variant="ghost" icon={Trash2} onClick={() => remove(entry)} loading={busy === `remove-${entry.id}`} data-testid={`shortlist-remove-${entry.id}`}>Quitar</Button>
                </div>
              </div>
            )
          })}
          {!rows.length && <p className="small muted">No hay objetivos con este filtro. Añade uno desde la búsqueda superior.</p>}
        </div>
      </Card>
    </>
  )
}
