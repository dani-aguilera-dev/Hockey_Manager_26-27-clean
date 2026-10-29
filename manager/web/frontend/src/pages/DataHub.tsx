import { useEffect, useMemo, useState } from 'react'
import { BarChart3, BrainCircuit, Save, ShieldAlert, Target } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { DatahubData, DatahubInstructionOption } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

export default function DataHubPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<DatahubData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const [instructions, setInstructions] = useState<Record<string, string>>({})

  function load() {
    setLoading(true)
    api.get<DatahubData>('/datahub')
      .then(({ data }) => {
        setData(data)
        const initial = { ...(data.instructions || {}) }
        for (const player of data.key_players || []) {
          if (!initial[player.id] && player.recommended_instruction) initial[player.id] = player.recommended_instruction
        }
        setInstructions(initial)
        setSaved(false)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el data hub.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function saveInstructions() {
    if (!data?.opponent) return
    setBusy(true)
    try {
      const response = await api.post<{ datahub: DatahubData; state: unknown }>('/datahub/instructions', {
        opponent_id: data.opponent.id,
        instructions,
      })
      setData(response.data.datahub)
      applyState(response.data.state as never)
      setSaved(true)
      toast(response.message || 'Instrucciones guardadas.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudieron guardar las instrucciones.', 'danger')
    } finally {
      setBusy(false)
    }
  }

  const effect = useMemo(() => {
    let attack = 0
    let defense = 0
    let players = 0
    for (const [playerId, instructionId] of Object.entries(instructions)) {
      const option = data?.options.find((item) => item.id === instructionId)
      if (!option || !data?.key_players?.some((player) => player.id === playerId)) continue
      attack += option.attack
      defense += option.defense
      players += 1
    }
    return { attack: Math.round(attack * 10) / 10, defense: Math.round(defense * 10) / 10, players }
  }, [instructions, data])

  if (loading) return <LoadingBlock label="Cruzando datos del rival…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el data hub.</p></Card>
  if (!data.fixture || !data.opponent || !data.user) {
    return (
      <>
        <PageHeader eyebrow="Data hub" title="Data hub e instrucciones" subtitle="Análisis del próximo rival y plan de partido." />
        <Card><p className="muted">{data.message || 'No hay un partido pendiente para analizar.'}</p></Card>
      </>
    )
  }

  const opponent = data.opponent
  const user = data.user
  const stats = opponent.stats

  return (
    <>
      <PageHeader
        eyebrow={`${data.competition?.short_name || ''} · ${dateLabel(data.fixture.date)} · ${data.fixture.user_is_home ? 'Casa' : 'Fuera'}`}
        title="Data hub e instrucciones"
        subtitle={`${data.fixture.home_name} vs ${data.fixture.away_name}. Analiza al rival, detecta amenazas y prepara instrucciones que afectan al motor de partido.`}
        actions={<>{saved && <Badge tone="ok" className="datahub-saved">Instrucciones guardadas</Badge>}<Button icon={BarChart3} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Rival" value={opponent.name} hint={`${opponent.city} · ${stats.position}º clasificado`} tone="blue" icon={Target} />
        <StatCard label="Forma" value={stats.form} hint={`${stats.wins}V ${stats.draws}E ${stats.losses}D`} tone="gold" />
        <StatCard label="Goles a favor" value={stats.goals_per_game} hint={`${stats.goals_for} en ${stats.played} partidos`} />
        <StatCard label="Goles en contra" value={stats.goals_against_per_game} hint={`Posesión media ${stats.possession}%`} tone="danger" icon={ShieldAlert} />
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">ANÁLISIS DEL RIVAL</div><h3 style={{ margin: '3px 0 0' }}>Qué esperar</h3></div>
            <BrainCircuit size={22} className="gold" />
          </div>
          <div className="stack-sm mt-2">
            {(data.analysis || []).map((line) => <div className="datahub-analysis" key={line}>{line}</div>)}
          </div>
          <div className="datahub-tactics mt-2">
            <Badge tone="neutral">Formación {opponent.tactics.formation}</Badge>
            <Badge tone="neutral">Mentalidad {opponent.tactics.mentality}</Badge>
            <Badge tone="neutral">Presión {opponent.tactics.press}</Badge>
            <Badge tone="neutral">Bloque {opponent.tactics.block}</Badge>
          </div>
        </Card>

        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">TU EQUIPO</div><h3 style={{ margin: '3px 0 0' }}>Comparativa</h3></div>
            <Badge tone="blue">{user.stats.form}</Badge>
          </div>
          <div className="datahub-compare mt-2">
            <div><span>Goles/partido</span><b>{user.stats.goals_per_game}</b><b>{stats.goals_per_game}</b></div>
            <div><span>Goles contra</span><b>{user.stats.goals_against_per_game}</b><b>{stats.goals_against_per_game}</b></div>
            <div><span>Posesión</span><b>{user.stats.possession}%</b><b>{stats.possession}%</b></div>
            <div><span>Tiros/partido</span><b>{user.stats.shots_per_game}</b><b>{stats.shots_per_game}</b></div>
            <div><span>PC/partido</span><b>{user.stats.pc_per_game}</b><b>{stats.pc_per_game}</b></div>
          </div>
          {opponent.availability.length > 0 && (
            <div className="mt-2"><div className="cat">BAJAS DEL RIVAL</div>{opponent.availability.map((item) => <p className="small muted" key={item.id}>{item.name} · {item.reason}</p>)}</div>
          )}
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">JUGADORES CLAVE E INSTRUCCIONES</div><h3 style={{ margin: '3px 0 0' }}>Plan de partido</h3></div>
          <Badge tone={effect.players ? 'gold' : 'neutral'}>Ataque rival −{effect.attack} · defensa −{effect.defense}</Badge>
        </div>
        <p className="small muted mt-1">Marca las instrucciones y guarda el plan. Se aplican al rival en el próximo partido y quedan registradas en la partida.</p>
        <div className="datahub-player-grid mt-2">
          {(data.key_players || []).map((player) => (
            <div className="datahub-player" key={player.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <Badge tone={player.status === 'Disponible' ? 'neutral' : 'danger'}>{player.status}</Badge>
                <Badge tone="blue">{player.threat}</Badge>
              </div>
              <h3>{player.name}</h3>
              <p className="small muted">{player.position} · {player.age} años · {player.overall} OVR · {player.goals} goles</p>
              <label className="field">
                <span>Instrucción</span>
                <select
                  data-testid={`instruction-${player.id}`}
                  value={instructions[player.id] || ''}
                  onChange={(event) => setInstructions({ ...instructions, [player.id]: event.target.value })}
                >
                  <option value="">Sin instrucción</option>
                  {(data.options || []).map((option: DatahubInstructionOption) => (
                    <option key={option.id} value={option.id}>{option.label}</option>
                  ))}
                </select>
              </label>
            </div>
          ))}
        </div>
        <div className="actions mt-2">
          <Button variant="primary" icon={Save} onClick={saveInstructions} loading={busy} data-testid="datahub-save">Guardar instrucciones</Button>
          <Button onClick={() => setInstructions({})}>Limpiar plan</Button>
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0 }}>Historial directo</h3>
          <Badge tone="neutral">{data.head_to_head?.length || 0} partidos</Badge>
        </div>
        <div className="stack-sm mt-2">
          {(data.head_to_head || []).map((match) => (
            <div className="datahub-h2h" key={`${match.date}-${match.round}`}>
              <span>{dateLabel(match.date)}</span><b>{match.home_name}</b><strong>{match.home_goals} - {match.away_goals}</strong><b>{match.away_name}</b>
            </div>
          ))}
          {!data.head_to_head?.length && <p className="small muted">No hay precedentes directos esta temporada.</p>}
        </div>
      </Card>
    </>
  )
}
