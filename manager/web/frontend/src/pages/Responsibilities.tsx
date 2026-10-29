import { useEffect, useState } from 'react'
import { CheckCircle2, ClipboardList, Save, Users } from 'lucide-react'
import { api } from '../lib/api'
import type { ResponsibilitiesData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, StatCard } from '../components/ui'

export default function ResponsibilitiesPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<ResponsibilitiesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [selections, setSelections] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState(false)

  function load() {
    setLoading(true)
    api.get<ResponsibilitiesData>('/responsibilities')
      .then(({ data }) => {
        setData(data)
        setSelections(Object.fromEntries(data.areas.map((area) => [area.id, area.staff_name || ''])))
        setSaved(false)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar las responsabilidades.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function saveArea(areaId: string) {
    setBusy(areaId)
    try {
      const response = await api.post<{ responsibilities: ResponsibilitiesData; state: unknown }>('/responsibilities', {
        area: areaId,
        staff_name: selections[areaId] || '',
      })
      setData(response.data.responsibilities)
      applyState(response.data.state as never)
      setSaved(true)
      toast(response.message || 'Responsabilidad actualizada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo actualizar la responsabilidad.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Organizando el cuerpo técnico…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar las responsabilidades.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Cuerpo técnico · áreas · entrenamiento"
        title="Responsabilidades del staff"
        subtitle="Asigna a cada área del club un responsable. Su valoración mejora las sesiones, el ojeo, la recuperación y el análisis."
        actions={<>{saved && <Badge tone="ok" className="responsibility-saved">Guardado</Badge>}<Button icon={ClipboardList} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Áreas cubiertas" value={`${data.assigned}/${data.total}`} hint="Responsables asignados" tone="blue" icon={CheckCircle2} />
        <StatCard label="Staff disponible" value={data.staff.length} hint="Miembros del cuerpo técnico" icon={Users} />
        <StatCard label="Mejor valoración" value={data.staff[0]?.rating || '—'} hint={data.staff[0]?.name || 'Sin staff'} tone="gold" />
        <StatCard label="Sin asignar" value={data.total - data.assigned} hint="Áreas pendientes" tone={data.assigned === data.total ? 'ok' : 'danger'} />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">MAPA DE RESPONSABILIDADES</div><h3 style={{ margin: '3px 0 0' }}>Quién lleva cada área</h3></div>
          <Badge tone="neutral">{data.assigned}/{data.total}</Badge>
        </div>
        <div className="responsibility-grid mt-2">
          {data.areas.map((area) => (
            <div className="responsibility-card" key={area.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <Badge tone={area.staff_name ? 'ok' : 'neutral'}>{area.staff_name ? `${area.staff_rating}/100` : 'Sin asignar'}</Badge>
                <span className="small muted">factor {area.bonus.toFixed(2)}</span>
              </div>
              <h3>{area.label}</h3>
              <p className="small muted">{area.description}</p>
              <Field label="Responsable">
                <select value={selections[area.id] ?? ''} onChange={(event) => setSelections({ ...selections, [area.id]: event.target.value })} data-testid={`responsibility-select-${area.id}`}>
                  <option value="">Sin asignar</option>
                  {area.options.map((member) => <option key={member.name} value={member.name}>{member.name} · {member.role} · {member.rating}</option>)}
                </select>
              </Field>
              <Button size="sm" variant="primary" icon={Save} onClick={() => saveArea(area.id)} loading={busy === area.id} data-testid={`responsibility-save-${area.id}`}>Guardar</Button>
            </div>
          ))}
        </div>
      </Card>

      <Card className="mt-2">
        <h3>Cuerpo técnico</h3>
        <div className="stack-sm mt-2">
          {data.staff.map((member) => <div className="responsibility-row" key={member.name}><span>{member.name}<small>{member.role}</small></span><b>{member.rating}/100</b></div>)}
          {!data.staff.length && <p className="small muted">No hay staff contratado.</p>}
        </div>
      </Card>
    </>
  )
}
