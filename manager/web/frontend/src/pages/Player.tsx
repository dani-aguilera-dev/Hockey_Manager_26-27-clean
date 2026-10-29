import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, BadgeEuro, Heart, MessageSquare, Pencil, ShieldCheck } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money, number } from '../lib/format'
import type { PlayerDetailPayload, PlayerEditorData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, Crest, Field, LoadingBlock, Modal, PageHeader, Progress } from '../components/ui'

const attrGroups: Array<[string, string[]]> = [
  ['Técnica', ['control', 'pase', 'conduccion', 'golpeo', 'flick', 'regate_3d', 'definicion']],
  ['Set pieces', ['aerial', 'pc_injection', 'pc_trap', 'pc_flick', 'pc_deflection', 'pc_first_runner', 'pc_gk_save', 'stroke_shot', 'stroke_save', 'free_hit']],
  ['Táctica', ['posicionamiento', 'pressing', 'cobertura', 'transicion', 'desmarque']],
  ['Física', ['velocidad', 'resistencia', 'fuerza', 'agilidad', 'coordinacion']],
  ['Mental', ['decisiones', 'concentracion', 'competitividad', 'liderazgo']],
  ['Portero', ['reflejos', 'blocaje', 'distribucion', 'uno_vs_uno', 'alto', 'rebote_gk']],
]

function labelAttr(key: string) {
  return key.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default function PlayerPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { game, applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<PlayerDetailPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [listingPrice, setListingPrice] = useState('')
  const [listingBusy, setListingBusy] = useState(false)
  const [editorOpen, setEditorOpen] = useState(false)
  const [editorBusy, setEditorBusy] = useState(false)
  const [editor, setEditor] = useState<PlayerEditorData | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api.get<PlayerDetailPayload>(`/player/${id}`)
      .then(({ data }) => {
        setData(data)
        setEditor(data.editor || null)
        setListingPrice(String(data.player.transfer_asking_price || data.player.value || 0))
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la ficha.', 'danger'))
      .finally(() => setLoading(false))
  }, [id, toast])

  async function toggleListing() {
    if (!data) return
    setListingBusy(true)
    const listed = !data.player.transfer_listed
    const asking = listed ? Number(listingPrice || data.player.value) : 0
    try {
      const response = await api.post<{ state: unknown }>(`/market/list/${data.player.id}`, { listed, asking_price: asking })
      applyState(response.data.state as never)
      setData((current) => current ? {
        ...current,
        player: { ...current.player, transfer_listed: listed, transfer_asking_price: asking },
      } : current)
      toast(response.message || (listed ? 'Jugador puesto en venta.' : 'Jugador retirado de la venta.'), 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo actualizar la venta.', 'danger')
    } finally {
      setListingBusy(false)
    }
  }

  async function saveEditor() {
    if (!data || !editor) return
    setEditorBusy(true)
    try {
      const response = await api.post<{ player: PlayerDetailPayload['player']; editor: PlayerEditorData; state: unknown }>(`/player/${data.player.id}/edit`, {
        changes: {
          name: editor.player.name,
          age: editor.player.age,
          position_group: editor.player.position_group,
          subposition: editor.player.subposition,
          archetype: editor.player.archetype,
          overall: editor.player.overall,
          potential: editor.player.potential,
          attributes: editor.player.attributes,
        },
      })
      setEditor(response.data.editor)
      setData((current) => current ? { ...current, player: response.data.player, editor: response.data.editor } : current)
      applyState(response.data.state as never)
      toast(response.message || 'Ficha actualizada.', 'success')
      setEditorOpen(false)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo editar la ficha.', 'danger')
    } finally {
      setEditorBusy(false)
    }
  }

  if (loading) return <LoadingBlock label="Cargando ficha del jugador…" />
  if (!data) return <Card><p className="muted">No se encontró el jugador.</p><Button onClick={() => navigate(-1)}>Volver</Button></Card>

  const { player, owner, owner_name, market } = data

  return (
    <>
      <PageHeader
        eyebrow={`${player.league_label} · ${player.archetype}`}
        title={player.name}
        subtitle={`${player.age} años · ${player.subposition} · ${player.origin_team ? `procede de ${player.origin_team}` : owner_name} · valor ${money(player.value)}`}
        actions={<><Button icon={ArrowLeft} onClick={() => navigate(-1)}>Volver</Button>{editor && <Button icon={Pencil} onClick={() => setEditorOpen(true)}>Editar ficha</Button>}{data.is_user && <Button variant="primary" icon={MessageSquare} onClick={() => navigate(`/game/chat?target_type=player&target_id=${encodeURIComponent(player.id)}`)}>Hablar</Button>}</>}
      />

      <section className="player-hero">
        <div className="player-hero-photo"><Avatar player={player} size={112} /></div>
        <div className="player-hero-main">
          <div className="inline">
            <Badge tone="gold">{player.overall.toFixed(1)} OVR</Badge>
            <Badge tone="blue">{player.stars} en {player.league_label}</Badge>
            <Badge tone={player.available ? 'ok' : 'danger'}>{player.available ? 'Disponible' : player.absence_label || 'Baja'}</Badge>
          </div>
          <p>{player.tier} · potencial {player.potential.toFixed(1)} · forma {player.form.toFixed(1)} · fatiga {player.fatigue.toFixed(0)}%</p>
          <div className="hero-kpis">
            <div className="hero-kpi"><span>Overall</span><b>{player.overall.toFixed(1)}</b></div>
            <div className="hero-kpi"><span>Potencial</span><b>{player.potential.toFixed(1)}</b></div>
            <div className="hero-kpi"><span>Partidos</span><b>{player.apps}</b></div>
            <div className="hero-kpi"><span>Goles</span><b>{player.season_goals}</b></div>
            <div className="hero-kpi"><span>Asist.</span><b>{player.season_assists}</b></div>
            <div className="hero-kpi"><span>Rating</span><b>{player.rating.toFixed(2)}</b></div>
            <div className="hero-kpi"><span>Relación</span><b>{player.relationship}</b><small>{player.relationship_label}</small></div>
          </div>
        </div>
        {owner && <Crest src={owner.crest} name={owner.name} size={62} />}
      </section>

      <div className="split-2 mt-2">
        <Card>
          <h3>Rendimiento</h3>
          <p className="small muted">{player.apps} PJ · {player.season_goals} goles · {player.season_assists} asistencias · moral {player.morale}/20</p>
          <div className="stack-sm mt-1">
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Relación con el entrenador</span><b className="small">{player.relationship}/100</b></div><Progress value={player.relationship} tone={player.relationship >= 60 ? 'ok' : 'gold'} /></div>
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Fatiga</span><b className="small">{player.fatigue.toFixed(0)}%</b></div><Progress value={player.fatigue} tone={player.fatigue > 60 ? 'danger' : 'blue'} /></div>
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Forma</span><b className="small">{player.form.toFixed(1)}/10</b></div><Progress value={player.form * 10} tone="gold" /></div>
          </div>
          <div className="inline mt-2">
            <Badge tone="neutral">Contrato {player.contract_until}</Badge>
            <Badge tone="neutral">{money(player.salary)} / año</Badge>
          </div>
        </Card>
        <Card>
          <h3>Estado y mercado</h3>
          <p className="small muted">
            {player.available
              ? 'Disponible para el próximo partido.'
              : player.injury > 0
                ? `${player.absence_label}. ${player.injury_type || 'Lesión'} (${player.injury_severity || 'leve'}) · ${player.injury} partido(s) de baja.`
                : `${player.absence_label}. ${player.suspension_reason || 'Sanción'} · ${player.suspension} partido(s) de baja.`}
          </p>
          {market ? (
            <>
              <div className="split-2 mt-1">
                <div><span className="small muted">Precio de salida</span><div className="hero-kpi"><b>{money(market.asking)}</b></div></div>
                <div><span className="small muted">Ojeador</span><div className="hero-kpi"><b>{market.scout}</b></div></div>
              </div>
              <p className="small muted mt-1">{market.window_text} · salario mínimo {money(market.minimum_salary)}.</p>
              <Button variant="primary" icon={BadgeEuro} onClick={() => navigate(`/game/market/player/${player.id}`)}>Abrir negociación</Button>
            </>
          ) : (
            <>
              <div className="inline mt-1"><Badge tone={player.transfer_listed ? 'gold' : 'neutral'}>{player.transfer_listed ? 'En venta' : 'No está en venta'}</Badge><span className="small muted">Relación {player.relationship}/100 · contrato {player.contract_until}</span></div>
              <div className="form-row mt-2">
                <Field label="Precio de salida"><input value={listingPrice} onChange={(event) => setListingPrice(event.target.value.replace(/\D/g, ''))} inputMode="numeric" /></Field>
                <Button variant={player.transfer_listed ? 'secondary' : 'primary'} icon={BadgeEuro} onClick={toggleListing} loading={listingBusy}>{player.transfer_listed ? 'Quitar de venta' : 'Poner en venta'}</Button>
              </div>
              <div className="notice notice-ok mt-2"><ShieldCheck size={16} /><div>Este jugador pertenece a tu plantilla. Puedes ponerlo en venta aquí o renovar su contrato desde Mercado → Renovar.</div></div>
            </>
          )}
        </Card>
      </div>

      <Card className="mt-2">
        <h3>Atributos</h3>
        <div className="attr-grid">
          {attrGroups.map(([group, keys]) => (
            <div className="attr-group" key={group}>
              <h3>{group}</h3>
              {keys.filter((key) => key in player.attributes).map((key) => (
                <div className="attr-row" key={key}>
                  <span>{labelAttr(key)}</span>
                  <div className="attr-bar"><span style={{ width: `${player.attributes[key]}%` }} /></div>
                  <b>{player.attributes[key]}</b>
                </div>
              ))}
            </div>
          ))}
        </div>
      </Card>

      {player.promises?.length ? (
        <Card className="mt-2">
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>Promesas</h3>
            <Badge tone="warn">{player.promises.filter((promise) => promise.status === 'open').length} abierta(s)</Badge>
          </div>
          <div className="stack-sm mt-2">
            {player.promises.map((promise, index) => (
              <div className="squad-status-row" key={`${String(promise.type)}-${index}`}>
                <span className="squad-status-main">
                  <b>{String(promise.text || 'Promesa')}</b>
                  <span>Hasta {dateLabel(String(promise.due || ''))} · {String(promise.status || 'open')}</span>
                </span>
                <Badge tone={promise.status === 'kept' ? 'ok' : promise.status === 'broken' ? 'danger' : 'warn'}>
                  {promise.status === 'kept' ? 'Cumplida' : promise.status === 'broken' ? 'Rota' : 'Pendiente'}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      <Card className="mt-2">
        <h3>Histórico por temporada</h3>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Temporada</th><th>Club</th><th>Liga</th><th className="num">PJ</th><th className="num">Goles</th><th className="num">Asist.</th><th className="num">Rating</th><th className="num">OVR</th></tr></thead>
            <tbody>
              {player.apps > 0 && <tr><td>{game?.game.season || 'Actual'}</td><td>{owner_name}</td><td>{player.league}</td><td className="num">{player.apps}</td><td className="num">{player.season_goals}</td><td className="num">{player.season_assists}</td><td className="num">{player.rating.toFixed(2)}</td><td className="num">{player.overall.toFixed(1)}</td></tr>}
              {player.career.length ? player.career.map((row, index) => (
                <tr key={`${row.season}-${index}`}><td>{row.season}</td><td>{row.club}</td><td>{row.league}</td><td className="num">{row.apps}</td><td className="num">{row.goals}</td><td className="num">{row.assists}</td><td className="num">{row.rating.toFixed(2)}</td><td className="num">{row.overall.toFixed(1)}</td></tr>
              )) : <tr><td colSpan={8} className="muted">Sin histórico anterior. La temporada actual se guardará al terminar.</td></tr>}
            </tbody>
          </table>
        </div>
      </Card>

      <Modal open={editorOpen} title="Editar ficha del jugador" onClose={() => setEditorOpen(false)} wide>
        {editor && (
          <div className="stack-sm">
            <div className="notice notice-info">
              <Pencil size={16} />
              <div>Corrige posiciones estimadas, atributos o datos básicos. El cambio queda registrado en la partida y no reinicia la temporada.</div>
            </div>
            <div className="form-row">
              <Field label="Nombre"><input value={editor.player.name} onChange={(event) => setEditor({ ...editor, player: { ...editor.player, name: event.target.value } })} /></Field>
              <Field label="Edad"><input type="number" min={14} max={50} value={editor.player.age} onChange={(event) => setEditor({ ...editor, player: { ...editor.player, age: Number(event.target.value) } })} /></Field>
            </div>
            <div className="form-row">
              <Field label="Línea">
                <select value={editor.player.position_group} onChange={(event) => setEditor({ ...editor, player: { ...editor.player, position_group: event.target.value } })}>
                  {editor.position_groups.map((group) => <option key={group} value={group}>{group}</option>)}
                </select>
              </Field>
              <Field label="Posición">
                <select value={editor.player.subposition} onChange={(event) => setEditor({ ...editor, player: { ...editor.player, subposition: event.target.value } })}>
                  {editor.subpositions.map((sub) => <option key={sub} value={sub}>{sub}</option>)}
                </select>
              </Field>
              <Field label="Arquetipo"><input value={editor.player.archetype} onChange={(event) => setEditor({ ...editor, player: { ...editor.player, archetype: event.target.value } })} /></Field>
            </div>
            <div className="form-row">
              <Field label="Overall"><input type="number" min={1} max={99} value={editor.player.overall} onChange={(event) => setEditor({ ...editor, player: { ...editor.player, overall: Number(event.target.value) } })} /></Field>
              <Field label="Potencial"><input type="number" min={1} max={99} value={editor.player.potential} onChange={(event) => setEditor({ ...editor, player: { ...editor.player, potential: Number(event.target.value) } })} /></Field>
            </div>
            <details>
              <summary className="small muted">Editar atributos ({Object.keys(editor.player.attributes).length})</summary>
              <div className="editor-attributes">
                {Object.entries(editor.player.attributes).sort(([a], [b]) => a.localeCompare(b)).map(([key, value]) => (
                  <label className="field" key={key}>
                    <span>{labelAttr(key)}</span>
                    <input
                      type="number"
                      min={1}
                      max={99}
                      value={value}
                      onChange={(event) => setEditor({
                        ...editor,
                        player: { ...editor.player, attributes: { ...editor.player.attributes, [key]: Number(event.target.value) } },
                      })}
                    />
                  </label>
                ))}
              </div>
            </details>
            <div className="actions mt-2">
              <Button variant="primary" icon={Pencil} onClick={saveEditor} loading={editorBusy}>Guardar cambios</Button>
              <Button onClick={() => setEditorOpen(false)}>Cancelar</Button>
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}

