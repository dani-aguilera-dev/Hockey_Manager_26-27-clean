import { useEffect, useState } from 'react'
import { Building2, Hammer, ShieldCheck, TrendingUp } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { FacilitiesData, FacilityUpgrade } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

export default function FacilitiesPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<FacilitiesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  function load() {
    setLoading(true)
    api.get<FacilitiesData>('/facilities')
      .then(({ data }) => {
        setData(data)
        setSaved(false)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar las instalaciones.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function upgrade(request: FacilityUpgrade) {
    setBusy(request.id)
    try {
      const response = await api.post<{ facilities: FacilitiesData; state: unknown }>('/facilities/upgrade', { request_id: request.id })
      setData(response.data.facilities)
      applyState(response.data.state as never)
      setSaved(true)
      toast(response.message || 'Mejora solicitada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo solicitar la mejora.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Revisando las instalaciones…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar las instalaciones.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Club · instalaciones · inversión"
        title="Instalaciones del club"
        subtitle="Estado del estadio, entrenamiento, cantera, médico, vídeo y ojeo. Solicita mejoras y revisa el historial de inversión."
        actions={<>{saved && <Badge tone="ok" className="facility-saved">Guardado</Badge>}<Button icon={Building2} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Nivel medio" value={`${data.summary.average}/100`} hint={`Mínimo ${data.summary.lowest} · máximo ${data.summary.highest}`} tone="blue" icon={TrendingUp} />
        <StatCard label="Estadio" value={data.stadium.name || '—'} hint={`${data.summary.capacity.toLocaleString('es-ES')} plazas`} tone="gold" icon={Building2} />
        <StatCard label="Cantera" value={data.academy_rating} hint="Academia del club" icon={ShieldCheck} />
        <StatCard label="Mejoras" value={data.summary.upgrades} hint="Inversiones registradas" icon={Hammer} />
      </div>

      <div className="facility-grid mt-2">
        {data.facilities.map((facility) => (
          <Card key={facility.id}>
            <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">{facility.level}</div><h3 style={{ margin: '3px 0 0' }}>{facility.label}</h3></div><b className="gold">{facility.value}</b></div>
            <p className="small muted mt-1">{facility.description}</p>
            <Progress value={facility.value} tone={facility.value >= 75 ? 'ok' : facility.value >= 55 ? 'gold' : 'danger'} />
          </Card>
        ))}
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">MEJORAS DISPONIBLES</div><h3 style={{ margin: '3px 0 0' }}>Inversión y proyecto</h3></div>
          <Badge tone="gold">{data.upgrades.filter((request) => request.available).length} disponibles</Badge>
        </div>
        <div className="facility-upgrade-grid mt-2">
          {data.upgrades.map((request) => (
            <div className="facility-upgrade" key={request.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}><Badge tone={request.available ? 'blue' : 'danger'}>{request.available ? 'Disponible' : 'Sin caja'}</Badge><span className="small muted">{Math.round(request.approval_chance * 100)}%</span></div>
              <h3>{request.label}</h3>
              <p className="small muted">{request.effect_text}</p>
              <div className="facility-upgrade-numbers"><span>Coste</span><b>{money(request.cost)}</b></div>
              <Button size="sm" variant="primary" icon={Hammer} onClick={() => upgrade(request)} loading={busy === request.id} disabled={!request.available} data-testid={`facility-upgrade-${request.id}`}>Solicitar mejora</Button>
            </div>
          ))}
          {!data.upgrades.length && <p className="small muted">No hay mejoras disponibles.</p>}
        </div>
      </Card>

      <Card className="mt-2">
        <h3>Historial de inversión</h3>
        <div className="stack-sm mt-2">
          {data.history.map((entry, index) => (
            <div className="facility-history-row" key={`${entry.date}-${entry.request_id}-${index}`}>
              <Badge tone={entry.approved ? 'ok' : 'danger'}>{entry.approved ? 'Aprobada' : 'Rechazada'}</Badge>
              <div><b>{entry.label}</b><span>{dateLabel(entry.date)} · {entry.message}</span></div>
              <b>{money(entry.cost)}</b>
            </div>
          ))}
          {!data.history.length && <p className="small muted">Todavía no hay inversiones registradas.</p>}
        </div>
      </Card>
    </>
  )
}
