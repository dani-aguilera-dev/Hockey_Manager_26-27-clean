import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Check, X } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { IncomingOffer } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, EmptyState, Field, LoadingBlock, PageHeader } from '../components/ui'

export default function OffersPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [offers, setOffers] = useState<IncomingOffer[]>([])
  const [counters, setCounters] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get<{ offers: IncomingOffer[]; state: unknown }>('/market/offers')
      setOffers(data.offers)
      setCounters(Object.fromEntries(data.offers.map((offer) => [offer.id, String(Math.round(offer.fee * 1.10))])))
      applyState(data.state as never)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudieron cargar las ofertas.', 'danger')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void load() }, [])

  async function action(offer: IncomingOffer, decision: 'accept' | 'reject') {
    setBusy(offer.id)
    try {
      const response = await api.post<{ state: unknown }>(`/market/offers/${offer.id}`, { action: decision })
      applyState(response.data.state as never)
      toast(response.message || (decision === 'accept' ? 'Oferta aceptada.' : 'Oferta rechazada.'), decision === 'accept' ? 'success' : 'info')
      await load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo procesar la oferta.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function counter(offer: IncomingOffer) {
    const fee = Number(counters[offer.id] || 0)
    if (!fee) {
      toast('Introduce una contraoferta válida.', 'warning')
      return
    }
    setBusy(`counter-${offer.id}`)
    try {
      const response = await api.post<{ state: unknown }>(`/market/offers/${offer.id}/counter`, { fee })
      applyState(response.data.state as never)
      toast(response.message || 'Contraoferta enviada.', 'info')
      await load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo enviar la contraoferta.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Mercado · ofertas recibidas"
        title="Ofertas por tus jugadores"
        subtitle="Decide si vendes, negocias o proteges al grupo. Una venta puede cambiar la plantilla y la moral."
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game/market')}>Volver al mercado</Button>}
      />
      {loading ? <LoadingBlock label="Cargando ofertas…" /> : offers.length ? (
        <div className="stack-sm">
          {offers.map((offer) => {
            const affordable = offer.buyer_budget === undefined || offer.buyer_budget >= offer.fee
            return (
            <Card key={offer.id}>
              <div className="inline" style={{ justifyContent: 'space-between', gap: 12 }}>
                <div className="inline">
                  <Avatar player={{ name: offer.player_name, initials: offer.player_name.split(' ').map((part) => part[0]).join('').slice(0, 2) }} size={46} />
                  <div><div className="cat">OFERTA DE {offer.from_club_name.toUpperCase()}</div><h3 style={{ margin: '3px 0' }}>{offer.player_name}</h3><span className="small muted">{money(offer.fee)} de traspaso · {money(offer.salary)} de salario · {offer.years} años · presupuesto {money(offer.buyer_budget || 0)}</span></div>
                </div>
                <Badge tone={affordable ? 'warn' : 'danger'}>{affordable ? 'Pendiente' : 'Sin fondos'}</Badge>
              </div>
              <div className="form-row mt-2">
                <Field label="Contraoferta (€)">
                  <input
                    value={counters[offer.id] || ''}
                    onChange={(event) => setCounters({ ...counters, [offer.id]: event.target.value.replace(/\D/g, '') })}
                    inputMode="numeric"
                  />
                </Field>
                <Button size="sm" variant="blue" onClick={() => counter(offer)} loading={busy === `counter-${offer.id}`}>Enviar contraoferta</Button>
              </div>
              <div className="actions mt-2">
                <Button variant="primary" icon={Check} onClick={() => action(offer, 'accept')} loading={busy === offer.id} disabled={!affordable}>Aceptar</Button>
                <Button icon={X} onClick={() => action(offer, 'reject')} loading={busy === offer.id}>Rechazar</Button>
              </div>
            </Card>
          )})}
        </div>
      ) : <EmptyState title="No hay ofertas" body="El mercado está tranquilo. Sigue compitiendo y los clubes llamarán." action={<Button onClick={() => navigate('/game/market')}>Volver al mercado</Button>} />}
    </>
  )
}
