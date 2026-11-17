import { useEffect, useState } from 'react'
import { CheckCircle2, Dumbbell, RotateCcw, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import type { TrainingPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../lib/i18n'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader } from '../components/ui'

const ATTRIBUTE_LABELS: Record<string, string> = {
  aerial: 'Juego aéreo',
  pc_injection: 'Saque de PC',
  pc_trap: 'Control de PC',
  pc_flick: 'Flick de PC',
  pc_deflection: 'Desvío de PC',
  pc_first_runner: 'Primer defensor de PC',
  pc_gk_save: 'Parada de PC',
  stroke_shot: 'Lanzamiento de stroke',
  stroke_save: 'Parada de stroke',
  free_hit: 'Golpe franco',
  control: 'Control',
  pase: 'Pase',
  conduccion: 'Conducción',
  golpeo: 'Golpeo',
  flick: 'Flick',
  regate_3d: 'Regate 3D',
  definicion: 'Definición',
  posicionamiento: 'Posicionamiento',
  pressing: 'Pressing',
  cobertura: 'Cobertura',
  transicion: 'Transición',
  desmarque: 'Desmarque',
  velocidad: 'Velocidad',
  resistencia: 'Resistencia',
  fuerza: 'Fuerza',
  agilidad: 'Agilidad',
  coordinacion: 'Coordinación',
  decisiones: 'Decisiones',
  concentracion: 'Concentración',
  competitividad: 'Competitividad',
  liderazgo: 'Liderazgo',
  reflejos: 'Reflejos',
  blocaje: 'Blocaje',
  distribucion: 'Distribución',
  uno_vs_uno: 'Uno contra uno',
  alto: 'Bola alta',
  rebote_gk: 'Rebote',
}

function attrLabel(key: string) {
  return ATTRIBUTE_LABELS[key] || key.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default function TrainingPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [data, setData] = useState<TrainingPayload | null>(null)
  const [plan, setPlan] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)

  useEffect(() => {
    api.get<TrainingPayload>('/training')
      .then(({ data }) => {
        setData(data)
        setPlan(data.default_plan)
      })
      .catch((err) => toast(err instanceof Error ? err.message : t('No se pudo cargar el entrenamiento.'), 'danger'))
      .finally(() => setLoading(false))
  }, [toast])

  async function apply(action: 'auto' | 'recovery' | 'edit') {
    setBusy(action)
    try {
      const body: Record<string, unknown> = { action }
      if (action === 'edit') plan.forEach((session, index) => { body[`session${index}`] = session })
      const response = await api.post<{ state: unknown; report: TrainingPayload['report']; plan: string[]; plan_name: string }>('/training', body)
      if (response.data.state) applyState(response.data.state as never)
      setData((current) => current ? { ...current, trained: true, report: response.data.report, default_plan: response.data.plan, plan_name: response.data.plan_name } : current)
      setPlan(response.data.plan)
      toast(response.message || t('Entrenamiento aplicado.'), 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo aplicar el plan.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label={t('Cargando plan semanal…')} />
  if (!data) return <Card><p className="muted">{t('No se pudo cargar el entrenamiento.')}</p></Card>

  const report = data.report
  return (
    <>
      <PageHeader
        eyebrow={t('Semana · {opponent}', { opponent: data.opponent?.name || t('sin rival confirmado') })}
        title={t('Entrenamiento semanal')}
        subtitle={t('Planifica las cinco sesiones. La carga, la moral y la preparación del rival condicionan el partido.')}
        actions={<Badge tone={data.trained ? 'ok' : 'warn'}>{data.trained ? t('Semana planificada') : t('Pendiente')}</Badge>}
      />

      {data.trained && report ? (
        <div className="split-2">
          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">{t('INFORME SEMANAL')}</div><h2 style={{ margin: '3px 0' }}>{data.plan_name}</h2></div><CheckCircle2 size={24} className="ok" /></div>
            <p className="muted small">{report.message || t('El grupo ha completado la semana de trabajo.')}</p>
            <div className="dashboard-kpis" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              <div className="stat-card"><span className="stat-top">{t('FATIGA')}</span><strong>{report.fatigue_before ?? '—'}% → {report.fatigue_after ?? '—'}%</strong></div>
              <div className="stat-card"><span className="stat-top">{t('MORAL')}</span><strong>{report.morale_before ?? '—'} → {report.morale_after ?? '—'}</strong></div>
              <div className="stat-card"><span className="stat-top">{t('PREPARACIÓN')}</span><strong>+{report.prep_bonus ?? 0}</strong></div>
            </div>
            {report.gains?.length ? <p className="small muted mt-2">{t('Progresos: {value}', { value: report.gains.slice(0, 8).map((gain) => `${gain.player} ${t(attrLabel(gain.attr))} +1`).join(' · ') })}</p> : null}
            {report.injuries?.length ? <p className="small danger mt-1">{t('Lesiones: {value}', { value: report.injuries.map((injury) => `${injury.player} (${injury.matches})`).join(', ') })}</p> : null}
          </Card>
          <Card>
            <h3>{t('Plan aplicado')}</h3>
            <div className="stack-sm">
              {data.days.map((day, index) => (
                <div className="squad-status-row" key={day}>
                  <span className="squad-status-main"><b>{day}</b><span>{t(data.sessions[plan[index]]?.label || plan[index])}</span></span>
                  <Badge tone="neutral">{data.sessions[plan[index]]?.short || '—'}</Badge>
                </div>
              ))}
            </div>
            <Button variant="ghost" className="mt-2" icon={RotateCcw} onClick={() => setData({ ...data, trained: false })}>{t('Preparar otra semana')}</Button>
          </Card>
        </div>
      ) : (
        <div className="split-2">
          <Card>
            <h3>{t('Plan automático')}</h3>
            <p className="small muted">{t('El segundo entrenador decide según rival, fatiga, moral y academia. Su rating es {source}.', { source: data.opponent ? t('el del cuerpo técnico') : t('interno') })}</p>
            <div className="actions">
              <Button variant="primary" icon={Sparkles} onClick={() => apply('auto')} loading={busy === 'auto'}>{t('Aplicar plan automático')}</Button>
              <Button icon={RotateCcw} onClick={() => apply('recovery')} loading={busy === 'recovery'}>{t('Semana de recuperación')}</Button>
            </div>
            <div className="notice notice-info mt-2">{t('Si no planificas, el segundo entrenador aplicará un plan automático antes del partido.')}</div>
          </Card>
          <Card>
            <h3>{t('Editar plan')}</h3>
            <div className="stack-sm">
              {data.days.map((day, index) => (
                <Field key={day} label={day}>
                  <select value={plan[index]} onChange={(event) => setPlan((current) => current.map((value, i) => i === index ? event.target.value : value))}>
                    {data.session_order.map((key) => <option key={key} value={key}>{t(data.sessions[key].label)}</option>)}
                  </select>
                </Field>
              ))}
            </div>
            <Button variant="blue" className="mt-2" icon={Dumbbell} onClick={() => apply('edit')} loading={busy === 'edit'}>{t('Aplicar plan editado')}</Button>
          </Card>
        </div>
      )}

      <Card className="mt-2">
        <h3>{t('Referencia rápida')}</h3>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>{t('Sesión')}</th><th className="num">{t('Fatiga')}</th><th>{t('Efecto')}</th></tr></thead>
            <tbody>
              {data.session_order.map((key) => (
                <tr key={key}><td>{t(data.sessions[key].label)}</td><td className="num">{data.sessions[key].fatigue > 0 ? '+' : ''}{data.sessions[key].fatigue}%</td><td className="muted">{data.sessions[key].attrs.map((attr) => t(attrLabel(attr))).join(', ')}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
