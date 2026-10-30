import { useEffect, useState } from 'react'
import { Lock, Save, ShieldCheck, Wallet } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { ClausePlayer, ClausesData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, StatCard } from '../components/ui'

type Draft = { clause: string; bonus: string }

const statusLabels: Record<string, string> = {
  sin_clausula: 'Sin cláusula',
  baja: 'Baja',
  protegida: 'Protegida',
  alta: 'Alta',
}

export default function ClausesPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<ClausesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [drafts, setDrafts] = useState<Record<string, Draft>>({})
  const [saved, setSaved] = useState(false)

  function load() {
    setLoading(true)
    api.get<ClausesData>('/clauses')
      .then(({ data }) => {
        setData(data)
        setDrafts(Object.fromEntries(data.players.map((player) => [player.id, {
          clause: String(player.release_clause || player.suggested_clause),
          bonus: String(player.renewal_bonus || player.suggested_bonus),
        }])))
        setSaved(false)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar las cláusulas.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function save(player: ClausePlayer) {
    const draft = drafts[player.id]
    if (!draft) return
    setBusy(player.id)
    try {
      const response = await api.post<{ clauses: ClausesData; state: unknown }>(`/clauses/${player.id}`, {
        release_clause: Number(draft.clause || 0),
        renewal_bonus: Number(draft.bonus || 0),
      })
      setData(response.data.clauses)
      applyState(response.data.state as never)
      setSaved(true)
      toast(response.message || 'Cláusula actualizada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo actualizar la cláusula.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Revisando cláusulas y primas…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar las cláusulas.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Contratos · cláusulas · primas"
        title="Cláusulas y primas"
        subtitle="Protege a tus jugadores con una cláusula de rescisión y registra la prima de renovación. La prima se paga desde la caja."
        actions={<>{saved && <Badge tone="ok" className="clause-saved">Guardado</Badge>}<Button icon={Lock} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Jugadores protegidos" value={`${data.summary.protected}/${data.summary.players}`} hint={`${data.summary.without_clause} sin cláusula`} tone="blue" icon={ShieldCheck} />
        <StatCard label="Valor de cláusulas" value={money(data.summary.total_clause)} hint="Suma de rescisión" tone="gold" icon={Lock} />
        <StatCard label="Primas pagadas" value={money(data.summary.total_bonus)} hint="Coste acumulado" tone="danger" icon={Wallet} />
        <StatCard label="Caja disponible" value={money(data.summary.budget)} hint="Para primas y fichajes" />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">CLÁUSULAS DE LA PLANTILLA</div><h3 style={{ margin: '3px 0 0' }}>Protección contractual</h3></div>
          <Badge tone="neutral">{data.players.length}</Badge>
        </div>
        <div className="table-wrap mt-2">
          <table className="data-table">
            <thead><tr><th>Jugador</th><th>Pos</th><th className="num">OVR</th><th className="num">Valor</th><th>Cláusula</th><th>Prima</th><th>Estado</th><th></th></tr></thead>
            <tbody>{data.players.map((player) => {
              const draft = drafts[player.id] || { clause: String(player.suggested_clause), bonus: String(player.suggested_bonus) }
              return (
                <tr key={player.id}>
                  <td>{player.name}</td><td>{player.position}</td><td className="num">{player.overall}</td><td className="num">{money(player.value)}</td>
                  <td><input className="clause-input" type="number" min={0} value={draft.clause} onChange={(event) => setDrafts({ ...drafts, [player.id]: { ...draft, clause: event.target.value } })} data-testid={`clause-value-${player.id}`} /></td>
                  <td><input className="clause-input" type="number" min={0} value={draft.bonus} onChange={(event) => setDrafts({ ...drafts, [player.id]: { ...draft, bonus: event.target.value } })} data-testid={`clause-bonus-${player.id}`} /></td>
                  <td><Badge tone={player.clause_status === 'sin_clausula' ? 'neutral' : player.clause_status === 'alta' ? 'ok' : 'gold'}>{statusLabels[player.clause_status] || player.clause_status}</Badge></td>
                  <td><Button size="sm" variant="primary" icon={Save} onClick={() => save(player)} loading={busy === player.id} data-testid={`clause-save-${player.id}`}>Guardar</Button></td>
                </tr>
              )
            })}</tbody>
          </table>
        </div>
        <p className="small muted mt-2">La prima de renovación se descuenta de la caja y mejora la relación con el jugador. La cláusula no puede superar cinco veces su valor.</p>
      </Card>
    </>
  )
}
