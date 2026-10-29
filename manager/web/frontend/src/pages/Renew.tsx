import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, FileSignature } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { Negotiation, Player } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, LoadingBlock, PageHeader } from '../components/ui'

export default function RenewPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [players, setPlayers] = useState<Player[]>([])
  const [forms, setForms] = useState<Record<string, { salary: string; years: string }>>({})
  const [negotiations, setNegotiations] = useState<Record<string, Negotiation>>({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)

  function refresh() {
    setLoading(true)
    api.get<{ players: Player[] }>('/market/renew')
      .then(({ data }) => {
        setPlayers(data.players)
        setForms(Object.fromEntries(data.players.map((player) => [player.id, { salary: String(player.salary), years: '3' }])))
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar los contratos.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { refresh() }, [toast])

  async function renew(player: Player) {
    const form = forms[player.id]
    if (!form) return
    setBusy(player.id)
    try {
      const response = await api.post<{ state?: unknown; negotiation?: Negotiation }>(`/market/renew-negotiate/${player.id}`, {
        salary: Number(form.salary),
        years: Number(form.years),
      })
      if (response.data.state) applyState(response.data.state as never)
      const negotiation = response.data.negotiation
      if (negotiation?.status === 'open') {
        setNegotiations((current) => ({ ...current, [player.id]: negotiation }))
        toast(response.message || 'El jugador ha presentado una contraoferta.', 'warning')
      } else {
        toast(response.message || 'Contrato renovado.', 'success')
        setNegotiations((current) => {
          const next = { ...current }
          delete next[player.id]
          return next
        })
        refresh()
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo renovar el contrato.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function respondRenewal(player: Player, action: 'accept' | 'counter' | 'walk') {
    const negotiation = negotiations[player.id]
    const form = forms[player.id]
    if (!negotiation || !form) return
    setBusy(`renew-${player.id}`)
    try {
      const response = await api.post<{ state?: unknown; negotiation?: Negotiation }>(`/market/negotiations/${negotiation.id}`, {
        action,
        salary: Number(form.salary),
        years: Number(form.years),
      })
      if (response.data.state) applyState(response.data.state as never)
      const next = response.data.negotiation
      if (next?.status === 'open') {
        setNegotiations((current) => ({ ...current, [player.id]: next }))
        if (next.counter) setForms((current) => ({ ...current, [player.id]: { salary: String(next.counter!.salary), years: String(next.counter!.years) } }))
        toast(response.message || 'Contraoferta actualizada.', 'info')
      } else {
        toast(response.message || 'Renovación cerrada.', 'success')
        setNegotiations((current) => {
          const copy = { ...current }
          delete copy[player.id]
          return copy
        })
        refresh()
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo continuar la renovación.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Mercado · contratos"
        title="Renovar contratos"
        subtitle="Protege a los jugadores importantes antes de que el mercado los ponga a tiro."
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game/market')}>Volver al mercado</Button>}
      />
      {loading ? <LoadingBlock label="Cargando contratos…" /> : (
        <div className="stack-sm">
          {players.map((player) => {
            const form = forms[player.id] || { salary: String(player.salary), years: '3' }
            return (
              <Card key={player.id}>
                <div className="inline" style={{ justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                  <div className="inline">
                    <Avatar player={player} size={44} />
                    <div><h3 style={{ margin: '2px 0' }}>{player.name}</h3><span className="small muted">{player.subposition} · {player.age} años · contrato {player.contract_until} · salario {money(player.salary)}</span></div>
                  </div>
                  <Badge tone={player.contract_until <= '2028-06-30' ? 'warn' : 'neutral'}>{player.contract_until}</Badge>
                </div>
                <div className="form-row mt-2">
                  <label className="field"><span>Nuevo salario anual</span><input value={form.salary} onChange={(event) => setForms({ ...forms, [player.id]: { ...form, salary: event.target.value.replace(/\D/g, '') } })} inputMode="numeric" /></label>
                  <label className="field"><span>Años</span><select value={form.years} onChange={(event) => setForms({ ...forms, [player.id]: { ...form, years: event.target.value } })}><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select></label>
                  <Button variant="primary" icon={FileSignature} onClick={() => renew(player)} loading={busy === player.id}>Renovar</Button>
                </div>
                {negotiations[player.id] && (
                  <div className="notice notice-warn mt-2">
                    <div>
                      <b>Ronda {negotiations[player.id].round}/{negotiations[player.id].max_rounds}: {negotiations[player.id].message}</b>
                      <p className="small" style={{ margin: '4px 0 8px' }}>
                        Pide {money(negotiations[player.id].ask.salary)} anuales. Tu oferta actual: {money(Number(form.salary || 0))}.
                      </p>
                      <div className="actions">
                        <Button size="sm" variant="primary" onClick={() => respondRenewal(player, 'accept')} loading={busy === `renew-${player.id}`}>Aceptar</Button>
                        <Button size="sm" onClick={() => respondRenewal(player, 'counter')} loading={busy === `renew-${player.id}`}>Contraoferta</Button>
                        <Button size="sm" variant="ghost" onClick={() => respondRenewal(player, 'walk')} loading={busy === `renew-${player.id}`}>Retirarse</Button>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </>
  )
}
