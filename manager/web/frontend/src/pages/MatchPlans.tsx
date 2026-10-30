import { useEffect, useState } from 'react'
import { ClipboardList, Power, Save, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { MatchPlan, MatchPlansData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, StatCard } from '../components/ui'

type Draft = { name: string; situation: string; from_minute: string; instructions: Record<string, string> }

function defaultDraft(): Draft {
  return {
    name: '',
    situation: 'leading',
    from_minute: '45',
    instructions: { mentality: 'defensiva' },
  }
}

export default function MatchPlansPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<MatchPlansData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [draft, setDraft] = useState<Draft>(defaultDraft())
  const [saved, setSaved] = useState(false)

  function load() {
    setLoading(true)
    api.get<MatchPlansData>('/match-plans')
      .then(({ data }) => {
        setData(data)
        setSaved(false)
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar los planes.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  function setInstruction(field: string, value: string) {
    const next = { ...draft.instructions }
    if (value) next[field] = value
    else delete next[field]
    setDraft({ ...draft, instructions: next })
  }

  async function createPlan() {
    setBusy('create')
    try {
      const response = await api.post<{ match_plans: MatchPlansData; state: unknown }>('/match-plans', {
        name: draft.name,
        situation: draft.situation,
        from_minute: Number(draft.from_minute || 45),
        instructions: draft.instructions,
        enabled: true,
      })
      setData(response.data.match_plans)
      applyState(response.data.state as never)
      setDraft(defaultDraft())
      setSaved(true)
      toast(response.message || 'Plan creado.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo crear el plan.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function togglePlan(plan: MatchPlan) {
    setBusy(`toggle-${plan.id}`)
    try {
      const response = await api.post<{ match_plans: MatchPlansData; state: unknown }>(`/match-plans/${plan.id}`, {
        name: plan.name,
        situation: plan.situation,
        from_minute: plan.from_minute,
        instructions: plan.instructions,
        enabled: !plan.enabled,
      })
      setData(response.data.match_plans)
      applyState(response.data.state as never)
      setSaved(true)
      toast(response.message || 'Plan actualizado.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo actualizar el plan.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function removePlan(plan: MatchPlan) {
    setBusy(`delete-${plan.id}`)
    try {
      const response = await api.delete<{ match_plans: MatchPlansData; state: unknown }>(`/match-plans/${plan.id}`)
      setData(response.data.match_plans)
      applyState(response.data.state as never)
      toast(response.message || 'Plan eliminado.', 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo eliminar el plan.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading && !data) return <LoadingBlock label="Preparando los planes de partido…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar los planes.</p></Card>

  return (
    <>
      <PageHeader
        eyebrow="Táctica · escenarios · banquillo"
        title="Planes de partido"
        subtitle="Define qué hacer si vas por delante, empatado o por detrás a partir de un minuto. El plan se activa solo y ajusta ataque y defensa sin cambiar tu táctica base."
        actions={<>{saved && <Badge tone="ok" className="match-plan-saved">Guardado</Badge>}<Button icon={ClipboardList} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Planes" value={data.summary.total} hint={`${data.summary.enabled} activos`} tone="blue" icon={ClipboardList} />
        <StatCard label="Por delante" value={data.summary.leading} hint="Proteger o sentenciar" tone="ok" />
        <StatCard label="Empatados" value={data.summary.drawing} hint="Buscar el gol" tone="gold" />
        <StatCard label="Por detrás" value={data.summary.trailing} hint="Arriesgar para remontar" tone="danger" />
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">NUEVO PLAN</div><h3 style={{ margin: '3px 0 0' }}>Condición e instrucciones</h3></div>
          <Badge tone="neutral">{data.plans.length}/{data.max_plans}</Badge>
        </div>
        <div className="match-plan-form mt-2">
          <Field label="Nombre"><input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} placeholder="Cerrar el partido…" data-testid="match-plan-name" /></Field>
          <Field label="Situación"><select value={draft.situation} onChange={(event) => setDraft({ ...draft, situation: event.target.value })} data-testid="match-plan-situation">{data.situations.map((situation) => <option key={situation.id} value={situation.id}>{situation.label}</option>)}</select></Field>
          <Field label="Desde el minuto"><input type="number" min={0} max={60} value={draft.from_minute} onChange={(event) => setDraft({ ...draft, from_minute: event.target.value })} data-testid="match-plan-minute" /></Field>
          {data.fields.map((field) => (
            <Field key={field.field} label={field.label}>
              <select value={draft.instructions[field.field] || ''} onChange={(event) => setInstruction(field.field, event.target.value)} data-testid={`match-plan-field-${field.field}`}>
                <option value="">Sin cambio</option>
                {field.options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </Field>
          ))}
        </div>
        <div className="actions mt-2"><Button variant="primary" icon={Save} onClick={createPlan} loading={busy === 'create'} disabled={!draft.name.trim() || data.plans.length >= data.max_plans} data-testid="match-plan-create">Crear plan</Button></div>
        <p className="small muted mt-1">El plan se evalúa en cada momento del partido. Si la situación y el minuto coinciden, se aplica el delta táctico y se registra en la crónica.</p>
      </Card>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">PLANES GUARDADOS</div><h3 style={{ margin: '3px 0 0' }}>Automatismos de partido</h3></div>
          <Badge tone="gold">{data.summary.enabled} activos</Badge>
        </div>
        <div className="match-plan-grid mt-2">
          {data.plans.map((plan) => (
            <div className={`match-plan-card ${plan.enabled ? 'enabled' : 'disabled'}`} key={plan.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <Badge tone={plan.enabled ? 'ok' : 'neutral'} className="match-plan-status">{plan.enabled ? 'Activo' : 'Desactivado'}</Badge>
                <span className="small muted">{plan.situation_label}</span>
              </div>
              <h3>{plan.name}</h3>
              <p className="small muted">Desde el minuto {plan.from_minute} · creado {dateLabel(plan.created)}</p>
              <div className="match-plan-instructions">
                {plan.instruction_labels.map((label) => <span key={label}>{label}</span>)}
              </div>
              <div className="actions">
                <Button size="sm" variant={plan.enabled ? 'ghost' : 'primary'} icon={Power} onClick={() => togglePlan(plan)} loading={busy === `toggle-${plan.id}`} data-testid={`match-plan-toggle-${plan.id}`}>{plan.enabled ? 'Desactivar' : 'Activar'}</Button>
                <Button size="sm" variant="ghost" icon={Trash2} onClick={() => removePlan(plan)} loading={busy === `delete-${plan.id}`} data-testid={`match-plan-delete-${plan.id}`}>Eliminar</Button>
              </div>
            </div>
          ))}
          {!data.plans.length && <p className="small muted">No hay planes guardados. Crea uno para automatizar un escenario.</p>}
        </div>
      </Card>
    </>
  )
}
