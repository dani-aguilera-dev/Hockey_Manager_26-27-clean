import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, BadgeEuro, Building2, Check, Megaphone, RefreshCw, Ticket, TrendingUp, Users, X } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { BrandData, BrandOffer, CommercialCampaign, CommercialData, PlayerBrandOffer, SponsorOffer } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

interface CommercialPayload {
  commercial: CommercialData
  brands: BrandData
  finance: { cash: number; sponsor_annual: number }
  team: { name: string; equipment_bonus: number }
}

export default function CommercialPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<CommercialPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [price, setPrice] = useState('')

  function load() {
    setLoading(true)
    api.get<CommercialPayload>('/commercial')
      .then(({ data }) => {
        setData(data)
        setPrice(String(data.commercial.ticket_price))
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el área comercial.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function sponsorAction(offer: SponsorOffer, action: 'accept' | 'reject') {
    setBusy(`sponsor-${offer.id}`)
    try {
      const response = await api.post<{ state: unknown }>(`/commercial/offers/${offer.id}`, { action })
      applyState(response.data.state as never)
      toast(response.message || (action === 'accept' ? 'Patrocinio firmado.' : 'Oferta rechazada.'), action === 'accept' ? 'success' : 'info')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo procesar el patrocinio.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function brandAction(offer: BrandOffer, action: 'accept' | 'reject') {
    setBusy(`brand-${offer.id}`)
    try {
      const response = await api.post<{ state: unknown }>(`/brands/${offer.id}`, { action })
      applyState(response.data.state as never)
      toast(response.message || (action === 'accept' ? 'Marca firmada.' : 'Oferta de marca rechazada.'), action === 'accept' ? 'success' : 'info')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo procesar la marca.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function playerBrandAction(offer: PlayerBrandOffer, action: 'accept' | 'reject') {
    setBusy(`player-brand-${offer.id}`)
    try {
      const response = await api.post<{ state: unknown }>(`/brands/players/${offer.id}`, { action })
      applyState(response.data.state as never)
      toast(response.message || (action === 'accept' ? 'Contrato individual firmado.' : 'Oferta individual rechazada.'), action === 'accept' ? 'success' : 'info')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo procesar el contrato individual.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function savePrice() {
    setBusy('ticket')
    try {
      const response = await api.post<{ state: unknown }>('/commercial/ticket', { price: Number(price) })
      applyState(response.data.state as never)
      toast(response.message || 'Precio actualizado.', 'success')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo actualizar el precio.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function launch(campaign: CommercialCampaign) {
    setBusy(`campaign-${campaign.id}`)
    try {
      const response = await api.post<{ state: unknown }>('/commercial/campaign', { campaign_id: campaign.id })
      applyState(response.data.state as never)
      toast(response.message || 'Campaña lanzada.', 'success')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo lanzar la campaña.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Cargando marca, patrocinios y taquilla…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el área comercial.</p></Card>

  const commercial = data.commercial
  return (
    <>
      <PageHeader
        eyebrow="Club · marca y negocio"
        title="Comercial y marca"
        subtitle="Patrocinadores, taquilla, merchandising, campañas y valor de marca. Todo lo que rodea al juego también paga las facturas."
        actions={<><Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button><Button icon={RefreshCw} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Marca" value={`${commercial.brand_score}/100`} hint={money(commercial.brand_value)} tone="gold" icon={TrendingUp} />
        <StatCard label="Afición" value={`${commercial.fan_confidence}/100`} hint="Base social y ambiente" icon={Users} />
        <StatCard label="Patrocinios" value={`${money(commercial.sponsor_annual)} / año`} hint={`${money(commercial.sponsor_round)} por jornada`} tone="blue" icon={Building2} />
        <StatCard label="Taquilla" value={`${commercial.ticket_price} €`} hint={`${money(commercial.ticket_estimate)} estimado / partido`} icon={Ticket} />
      </div>

      <div className="commercial-hero">
        <div>
          <div className="cat">MARCA DEL CLUB</div>
          <h2>{data.team.name}</h2>
          <p className="small muted">La marca crece con resultados, afición, academia, jugadores y patrocinios. También puede caer con malas rachas.</p>
          <Progress value={commercial.brand_score} tone={commercial.brand_score >= 65 ? 'ok' : 'gold'} />
        </div>
        <div className="commercial-hero-score"><b>{commercial.brand_score}</b><span>Brand score</span></div>
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">PATROCINADORES ACTIVOS</div><h3 style={{ margin: '3px 0 0' }}>{commercial.active_deals.length} acuerdos</h3></div><Badge tone="ok">{money(commercial.sponsor_round)}/jornada</Badge></div>
          <div className="stack-sm mt-2">
            {commercial.active_deals.map((deal) => (
              <div className="sponsor-row" key={deal.id}>
                <span className="sponsor-mark"><Building2 size={17} /></span>
                <span className="sponsor-main"><b>{deal.name}</b><span>{deal.category} · {deal.tier_label} · hasta {deal.end || '—'}</span></span>
                <b className="gold">{money(deal.annual)}</b>
              </div>
            ))}
            {!commercial.active_deals.length && <p className="small muted">Todavía no hay acuerdos firmados. Revisa las ofertas.</p>}
          </div>
        </Card>
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">TAQUILLA Y MERCHANDISING</div><h3 style={{ margin: '3px 0 0' }}>Precio de entrada</h3></div><Badge tone="neutral">{commercial.merchandising}/100 merch</Badge></div>
          <p className="small muted mt-1">Subir el precio aumenta el ingreso por entrada, pero puede enfriar la asistencia. Bajarlo protege el ambiente.</p>
          <div className="form-row mt-2">
            <label className="field"><span>Entrada (€)</span><input value={price} onChange={(event) => setPrice(event.target.value.replace(/\D/g, ''))} inputMode="numeric" /></label>
            <Button variant="primary" icon={Ticket} onClick={savePrice} loading={busy === 'ticket'}>Guardar precio</Button>
          </div>
          <div className="stack-sm mt-2"><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Ingreso estimado por partido</span><b>{money(commercial.ticket_estimate)}</b></div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Merchandising por jornada</span><b>{money(commercial.merchandising_round)}</b></div></div>
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">OFERTAS DE PATROCINIO</div><h3 style={{ margin: '3px 0 0' }}>{commercial.offers.length} propuestas sobre la mesa</h3></div><Badge tone={commercial.offers.length ? 'gold' : 'neutral'}>{commercial.offers.length}</Badge></div>
        <div className="sponsor-offer-grid mt-2">
          {commercial.offers.map((offer) => (
            <div className="sponsor-offer" key={offer.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><Badge tone="gold">{offer.tier_label}</Badge><span className="small muted">{offer.years} años</span></div>
              <h3>{offer.name}</h3>
              <p className="small muted">{offer.category} · {offer.requirement}</p>
              <div className="sponsor-offer-numbers"><div><span>Anual</span><b>{money(offer.annual)}</b></div><div><span>Por jornada</span><b>{money(offer.per_round)}</b></div><div><span>Firma</span><b>{money(offer.signing_bonus)}</b></div></div>
              <div className="actions mt-2"><Button size="sm" variant="primary" icon={Check} onClick={() => sponsorAction(offer, 'accept')} loading={busy === `sponsor-${offer.id}`}>Firmar</Button><Button size="sm" icon={X} onClick={() => sponsorAction(offer, 'reject')} loading={busy === `sponsor-${offer.id}`}>Rechazar</Button></div>
            </div>
          ))}
          {!commercial.offers.length && <p className="small muted">No hay ofertas nuevas. La próxima llegará con la simulación.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">EQUIPACIÓN · MARCAS REALES DE HOCKEY</div><h3 style={{ margin: '3px 0 0' }}>{data.brands.active_deals.length} acuerdos de material</h3></div>
          <Badge tone="blue">Bonus equipación +{data.brands.equipment_bonus.toFixed(1)}</Badge>
        </div>
        <div className="stack-sm mt-2">
          {data.brands.active_deals.map((deal) => (
            <div className="sponsor-row" key={deal.id}>
              <span className="sponsor-mark"><Building2 size={17} /></span>
              <span className="sponsor-main"><b>{deal.brand}</b><span>{(deal.categories || []).join(' · ')} · hasta {deal.end || '—'}</span></span>
              <b className="gold">{money(deal.annual)}</b>
            </div>
          ))}
          {!data.brands.active_deals.length && <p className="small muted">Todavía no hay marca de equipación. Firma una oferta para mejorar material, caja y marca.</p>}
        </div>
        <div className="sponsor-offer-grid mt-2">
          {data.brands.offers.map((offer) => (
            <div className="sponsor-offer" key={offer.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><Badge tone="blue">{offer.tier_label || offer.tier}</Badge><span className="small muted">{offer.years} años</span></div>
              <h3>{offer.brand}</h3>
              <p className="small muted">{(offer.categories || []).join(' · ')} · {offer.requirement}</p>
              <p className="small muted">{offer.description}</p>
              <div className="sponsor-offer-numbers"><div><span>Anual</span><b>{money(offer.annual)}</b></div><div><span>Firma</span><b>{money(offer.signing_bonus || 0)}</b></div><div><span>Bonus</span><b>+{Number(offer.bonus || 0).toFixed(1)}</b></div></div>
              <div className="actions mt-2"><Button size="sm" variant="primary" icon={Check} onClick={() => brandAction(offer, 'accept')} loading={busy === `brand-${offer.id}`}>Firmar marca</Button><Button size="sm" icon={X} onClick={() => brandAction(offer, 'reject')} loading={busy === `brand-${offer.id}`}>Rechazar</Button></div>
            </div>
          ))}
          {!data.brands.offers.length && <p className="small muted">No hay ofertas de equipación nuevas. La próxima llegará con la simulación.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">CONTRATOS INDIVIDUALES DE IMAGEN</div><h3 style={{ margin: '3px 0 0' }}>{data.brands.player_deals.length} jugadores con marca personal</h3></div>
          <Badge tone="gold">Marca personal</Badge>
        </div>
        <div className="stack-sm mt-2">
          {data.brands.player_deals.map((deal) => (
            <div className="sponsor-row" key={`${deal.player_id}-${deal.id}`}>
              <span className="sponsor-mark"><Building2 size={17} /></span>
              <span className="sponsor-main"><b>{deal.player_name} · {deal.brand}</b><span>{(deal.categories || []).join(' · ')} · hasta {deal.end || '—'}</span></span>
              <b className="gold">{money(deal.annual)}</b>
            </div>
          ))}
          {!data.brands.player_deals.length && <p className="small muted">Ningún jugador tiene contrato de imagen individual. Firma una oferta para vincular marca y plantilla.</p>}
        </div>
        <div className="sponsor-offer-grid mt-2">
          {data.brands.player_offers.map((offer) => (
            <div className="sponsor-offer" key={offer.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><Badge tone="gold">{offer.tier_label || offer.tier}</Badge><span className="small muted">{offer.years} años</span></div>
              <h3>{offer.player_name}</h3>
              <p className="small muted">{offer.brand} · {(offer.categories || []).join(' · ')}</p>
              <div className="sponsor-offer-numbers"><div><span>Anual</span><b>{money(offer.annual)}</b></div><div><span>Firma</span><b>{money(offer.signing_bonus || 0)}</b></div><div><span>Bonus</span><b>+{Number(offer.bonus || 0).toFixed(1)}</b></div></div>
              <div className="actions mt-2"><Button size="sm" variant="primary" icon={Check} onClick={() => playerBrandAction(offer, 'accept')} loading={busy === `player-brand-${offer.id}`}>Firmar</Button><Button size="sm" icon={X} onClick={() => playerBrandAction(offer, 'reject')} loading={busy === `player-brand-${offer.id}`}>Rechazar</Button></div>
            </div>
          ))}
          {!data.brands.player_offers.length && <p className="small muted">No hay ofertas individuales nuevas. La próxima llegará con la simulación.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">CAMPAÑAS DE MARCA</div><h3 style={{ margin: '3px 0 0' }}>Invierte caja, gana marca y afición</h3></div><Megaphone size={22} className="gold" /></div>
        <div className="sponsor-offer-grid mt-2">
          {commercial.campaigns.map((campaign) => (
            <div className="sponsor-offer" key={campaign.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><Badge tone="blue">{campaign.label}</Badge><span className="small muted">{money(campaign.cost)}</span></div>
              <p className="small muted">{campaign.desc}</p>
              <div className="inline"><Badge tone="ok">Marca +{campaign.brand}</Badge><Badge tone="gold">Afición +{campaign.fan}</Badge></div>
              <Button size="sm" className="mt-2" variant="primary" icon={BadgeEuro} onClick={() => launch(campaign)} loading={busy === `campaign-${campaign.id}`} disabled={!campaign.affordable}>Lanzar campaña</Button>
            </div>
          ))}
        </div>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Historial comercial</h3><Badge tone="neutral">{commercial.history.length} movimientos</Badge></div>
        <div className="stack-sm mt-2">
          {commercial.history.slice().reverse().map((item, index) => (
            <div className="inbox-item" key={`${item.date}-${index}`}><b>{item.name}</b><span>{item.type} · {item.date}</span><p>{item.message}</p></div>
          ))}
          {!commercial.history.length && <p className="small muted">Todavía no hay movimientos comerciales.</p>}
        </div>
      </Card>
    </>
  )
}
