import { useEffect, useMemo, useState } from 'react'
import { ArrowUpCircle, Check, Save, Search, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import type { Player, Tactics, TacticsPayload } from '../types'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, Field, LoadingBlock, Modal, PageHeader } from '../components/ui'
import { Pitch } from '../components/Pitch'

const mentality = ['muy_defensiva', 'defensiva', 'equilibrada', 'ofensiva', 'muy_ofensiva']
const press = ['baja', 'media', 'alta', 'muy_alta']
const width = ['estrecha', 'normal', 'ancha']
const tempo = ['lento', 'normal', 'rapido']
const passing = ['corto', 'mixto', 'directo']
const defensiveSystems: Array<[string, string]> = [
  ['zona_baja', 'Zona baja · low block'],
  ['zona_media', 'Zona media · mid block'],
  ['zona_alta', 'Zona alta · high block'],
  ['individual_todo_campo', 'Individual todo el campo'],
  ['individual_mixta', 'Individual mixta · match-up'],
]
const attackSystems: Array<[string, string]> = [
  ['posicional', 'Ataque posicional'],
  ['contraataque', 'Contraataque'],
  ['directo', 'Juego directo'],
  ['bandas', 'Juego por bandas'],
  ['interior', 'Juego interior'],
  ['sobrecarga_derecha', 'Sobrecarga derecha'],
  ['sobrecarga_izquierda', 'Sobrecarga izquierda'],
]
const outlets: Array<[string, string]> = [
  ['portero', 'Salida con portero'],
  ['central', 'Salida por central'],
  ['lateral', 'Salida por lateral'],
  ['directo', 'Salida directa'],
]
const triggers: Array<[string, string]> = [
  ['perdida', 'Presión tras pérdida'],
  ['saque_fondo', 'Presión al saque de fondo'],
  ['banda', 'Presión en banda'],
  ['pase_atras', 'Presión al pase atrás'],
  ['siempre', 'Presión constante'],
]
const pcRoutines: Array<[string, string]> = [
  ['directa', 'Flick directo'],
  ['slip_izquierda', 'Slip izquierda'],
  ['slip_derecha', 'Slip derecha'],
  ['desvio', 'Desvío'],
  ['rebote', 'Rebote'],
  ['variacion', 'Variación'],
]
const specialistRoles: Array<[keyof Tactics, string]> = [
  ['pc_injector_id', 'Sacador · injector'],
  ['pc_stopper_id', 'Parador · stopper'],
  ['pc_flicker_id', 'Tirador · flicker'],
  ['pc_deflector_id', 'Desviador'],
  ['pc_rebounder_id', 'Rechace · rebounder'],
  ['pc_first_runner_id', 'Primer defensor de PC'],
  ['pc_goalkeeper_id', 'Portero de PC'],
  ['stroke_taker_id', 'Lanzador de penalty stroke'],
  ['stroke_goalkeeper_id', 'Portero de penalty stroke'],
  ['free_hit_taker_id', 'Especialista en golpes francos'],
]

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default function TacticsPage() {
  const { toast } = useToast()
  const [data, setData] = useState<TacticsPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tactics, setTactics] = useState<Tactics | null>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [pickerSlot, setPickerSlot] = useState<number | null>(null)
  const [pickerQuery, setPickerQuery] = useState('')
  const [promotePlayer, setPromotePlayer] = useState<Player | null>(null)

  useEffect(() => {
    api.get<TacticsPayload>('/tactics')
      .then(({ data }) => {
        setData(data)
        setTactics(data.tactics)
        setSelected(data.line.map((player) => player.id))
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la táctica.', 'danger'))
      .finally(() => setLoading(false))
  }, [toast])

  const playerMap = useMemo(() => {
    const map = new Map<string, Player>()
    data?.available.forEach((player) => map.set(player.id, player))
    data?.line.forEach((player) => map.set(player.id, player))
    data?.bench.forEach((player) => map.set(player.id, player))
    data?.slot_options.flat().forEach((player) => map.set(player.id, player))
    return map
  }, [data])

  const displayRows = useMemo(() => {
    if (!data) return []
    return data.slot_rows.map((row) => ({
      ...row,
      slots: row.slots.map((slot) => ({
        ...slot,
        player: selected[slot.index] ? playerMap.get(selected[slot.index]) || slot.player : slot.player,
      })),
    }))
  }, [data, selected, playerMap])

  const specialistPool = useMemo(() => {
    if (!data) return []
    const unique = new Map<string, Player>()
    data.squad.forEach((player) => unique.set(player.id, player))
    data.line.forEach((player) => unique.set(player.id, player))
    data.bench.forEach((player) => unique.set(player.id, player))
    return [...unique.values()].sort((a, b) => b.overall - a.overall)
  }, [data])

  function setField<K extends keyof Tactics>(key: K, value: Tactics[K]) {
    setTactics((current) => (current ? { ...current, [key]: value } : current))
  }

  const allSlots = useMemo(() => displayRows.flatMap((row) => row.slots), [displayRows])
  const pickerSlotData = pickerSlot === null ? null : allSlots.find((slot) => slot.index === pickerSlot) || null
  const pickerCandidates = useMemo(() => {
    if (!data || pickerSlot === null) return []
    const recommended = data.slot_options[pickerSlot] || []
    const recommendedIds = new Set(recommended.map((player) => player.id))
    const rest = data.squad.filter((player) => !recommendedIds.has(player.id)).sort((a, b) => b.overall - a.overall)
    const needle = pickerQuery.trim().toLowerCase()
    return [...recommended, ...rest].filter((player) => !needle || [player.name, player.subposition, player.archetype].some((value) => value.toLowerCase().includes(needle)))
  }, [data, pickerSlot, pickerQuery])

  function choosePlayer(index: number, playerId: string) {
    setSelected((current) => {
      const next = [...current]
      const previous = next[index]
      const existing = next.indexOf(playerId)
      if (existing >= 0 && existing !== index) next[existing] = previous
      next[index] = playerId
      return next
    })
    setPickerSlot(null)
    setPickerQuery('')
  }

  async function save(auto = false) {
    if (!tactics) return
    setSaving(true)
    try {
      const body: Record<string, unknown> = { ...tactics, auto }
      if (!auto) selected.forEach((playerId, index) => { body[`slot_${index}`] = playerId })
      const response = await api.post<TacticsPayload & { state: unknown }>('/tactics', body)
      setData(response.data)
      setTactics(response.data.tactics)
      setSelected(response.data.line.map((player) => player.id))
      toast(response.message || 'Once guardado.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo guardar la táctica.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingBlock label="Cargando pizarra y plantilla…" />
  if (!data || !tactics) return <Card><p className="muted">No se pudo cargar la táctica.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Pizarra · una decisión por partido"
        title="Táctica y once"
        subtitle="Sistema de hockey: bloque y marcaje, salida, ataque, presión y roles manuales de penalty corner y stroke."
        actions={
          <>
            <Button icon={Sparkles} onClick={() => save(true)} loading={saving}>Autoalineación</Button>
            <Button variant="primary" icon={Save} onClick={() => save(false)} loading={saving}>Guardar once</Button>
          </>
        }
      />

      <div className="tactics-layout">
        <div className="stack">
          <Card>
            <h3>Planteamiento</h3>
            <div className="form-grid tactics-form">
              <Field label="Formación"><select value={tactics.formation} onChange={(event) => setField('formation', event.target.value)}>{data.formations.map((value) => <option key={value}>{value}</option>)}</select></Field>
              <Field label="Mentalidad"><select value={tactics.mentality} onChange={(event) => setField('mentality', event.target.value)}>{mentality.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></Field>
              <Field label="Presión"><select value={tactics.press} onChange={(event) => setField('press', event.target.value)}>{press.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></Field>
              <Field label="Sistema defensivo"><select value={tactics.defensive_system} onChange={(event) => setField('defensive_system', event.target.value)}>{defensiveSystems.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></Field>
              <Field label="Sistema de ataque"><select value={tactics.attack_system} onChange={(event) => setField('attack_system', event.target.value)}>{attackSystems.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></Field>
              <Field label="Salida / build-up"><select value={tactics.outlet} onChange={(event) => setField('outlet', event.target.value)}>{outlets.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></Field>
              <Field label="Activador de presión"><select value={tactics.press_trigger} onChange={(event) => setField('press_trigger', event.target.value)}>{triggers.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></Field>
              <Field label="Anchura"><select value={tactics.width} onChange={(event) => setField('width', event.target.value)}>{width.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></Field>
              <Field label="Tempo"><select value={tactics.tempo} onChange={(event) => setField('tempo', event.target.value)}>{tempo.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></Field>
              <Field label="Pase"><select value={tactics.passing} onChange={(event) => setField('passing', event.target.value)}>{passing.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></Field>
            </div>
            <div className="notice notice-info mt-2">El once manual se mantiene hasta que cambies de formación. Si cambias de dibujo, el cuerpo técnico autoalinea.</div>
          </Card>
          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}>
              <div><div className="cat">BALÓN PARADO</div><h3 style={{ margin: '3px 0 0' }}>Penalty corner y stroke</h3></div>
              <Badge tone="gold">Roles manuales</Badge>
            </div>
            <div className="form-grid tactics-form mt-1">
              <Field label="Rutina de PC"><select value={tactics.pc_routine} onChange={(event) => setField('pc_routine', event.target.value)}>{pcRoutines.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></Field>
              {specialistRoles.map(([field, labelText]) => (
                <Field key={field} label={labelText}>
                  <select value={String(tactics[field] || '')} onChange={(event) => setField(field, event.target.value)}>
                    <option value="">Automático · mejor atributo</option>
                    {specialistPool.map((player) => (
                      <option key={player.id} value={player.id}>{player.name} · {player.subposition} · {player.overall.toFixed(1)}</option>
                    ))}
                  </select>
                </Field>
              ))}
            </div>
            <p className="small muted mt-1">El sacador, parador, tirador, desviador y jugador de rechace se usan en el próximo PC. El lanzador de stroke también se aplica a la tanda de penaltis.</p>
          </Card>
          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Banquillo</h3><Badge tone="neutral">{data.bench.length}</Badge></div>
            <div className="stack-sm mt-1">
              {data.bench.map((player) => <PlayerMini key={player.id} player={player} onPromote={() => setPromotePlayer(player)} />)}
            </div>
          </Card>
        </div>

        <div className="stack">
          <Card padded={false}>
            <div style={{ padding: '18px 18px 0' }}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <div><div className="cat">ONCE ACTUAL</div><h3 style={{ margin: '3px 0 0' }}>{tactics.formation}</h3></div>
                <Badge tone="gold">{selected.length}/11</Badge>
              </div>
            </div>
            <Pitch rows={displayRows} formation={tactics.formation} selectable activeSlot={pickerSlot} onSlotClick={(index) => { setPickerQuery(''); setPickerSlot(index) }} />
          </Card>
        </div>
      </div>

      <Modal
        open={pickerSlot !== null}
        title={pickerSlotData ? `Elegir ${pickerSlotData.code} · ${pickerSlotData.group}` : 'Elegir jugador'}
        onClose={() => { setPickerSlot(null); setPickerQuery('') }}
        wide
      >
        <div className="player-picker-head">
          <label className="search-box"><Search size={15} /><input value={pickerQuery} onChange={(event) => setPickerQuery(event.target.value)} placeholder="Buscar por nombre, posición o arquetipo…" /></label>
          <span className="small muted">{pickerCandidates.length} jugadores disponibles</span>
        </div>
        <div className="player-picker-list">
          {pickerCandidates.map((player) => {
            const recommended = data.slot_options[pickerSlot ?? 0]?.slice(0, 5).some((item) => item.id === player.id)
            const inLineup = selected.includes(player.id)
            const current = pickerSlotData?.player?.id === player.id
            return (
              <button type="button" className={`player-picker-row ${current ? 'current' : ''}`} key={player.id} onClick={() => choosePlayer(pickerSlot ?? 0, player.id)}>
                <Avatar player={player} size={42} />
                <span className="player-picker-main">
                  <span className="inline"><b>{player.name}</b>{recommended && <Badge tone="gold">Recomendado</Badge>}{inLineup && !current && <Badge tone="blue">En el once</Badge>}{current && <Badge tone="ok">Actual</Badge>}</span>
                  <span>{player.subposition} · {player.archetype} · {player.age} años</span>
                  <span className="small muted">OVR {player.overall.toFixed(1)} · forma {player.form.toFixed(1)} · fatiga {player.fatigue.toFixed(0)}% · relación {player.relationship}/100</span>
                </span>
                <span className="player-picker-side"><b>{player.overall.toFixed(1)}</b><span>{player.available ? 'Disponible' : player.absence_label}</span></span>
                {current ? <Check size={16} className="ok" /> : <span className="picker-arrow">Elegir</span>}
              </button>
            )
          })}
          {!pickerCandidates.length && <p className="small muted">No hay jugadores que coincidan con la búsqueda.</p>}
        </div>
      </Modal>

      <Modal
        open={Boolean(promotePlayer)}
        title={`Promover al once · ${promotePlayer?.name || ''}`}
        onClose={() => setPromotePlayer(null)}
        wide
      >
        <p className="small muted">Elige qué posición ocupa. El jugador que esté en esa posición pasará al banquillo.</p>
        <div className="player-picker-list mt-2">
          {allSlots.map((slot) => (
            <button type="button" className="player-picker-row" key={slot.index} onClick={() => { if (promotePlayer) choosePlayer(slot.index, promotePlayer.id); setPromotePlayer(null) }}>
              <span className="slot-code-pill">{slot.code}</span>
              <span className="player-picker-main"><b>{slot.group}</b><span>{slot.player?.name || 'Vacío'} · {slot.player?.subposition || '—'}</span></span>
              <span className="picker-arrow">Ocupar</span>
            </button>
          ))}
        </div>
      </Modal>
    </>
  )
}

function PlayerMini({ player, onPromote }: { player: Player; onPromote?: () => void }) {
  return (
    <div className="squad-status-row">
      <Avatar player={player} size={30} />
      <span className="squad-status-main"><b>{player.name}</b><span>{player.subposition} · {player.archetype} · fatiga {player.fatigue.toFixed(0)}%</span></span>
      <Badge tone="neutral">{player.overall.toFixed(1)}</Badge>
      {onPromote && <Button size="sm" variant="ghost" icon={ArrowUpCircle} onClick={onPromote}>Al once</Button>}
    </div>
  )
}
