import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Compass, RefreshCw, Search, Sparkles } from 'lucide-react'
import { api, queryString } from '../lib/api'
import { money } from '../lib/format'
import type { ScoutData } from '../types'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../lib/i18n'
import { Avatar, Badge, Button, Card, EmptyState, Field, LoadingBlock } from '../components/ui'

export default function ScoutPanel({ onUseMarket }: { onUseMarket: () => void }) {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [data, setData] = useState<ScoutData | null>(null)
  const [loading, setLoading] = useState(true)
  const [focus, setFocus] = useState('equilibrado')
  const [maxAge, setMaxAge] = useState('')
  const [position, setPosition] = useState('')

  function load() {
    setLoading(true)
    api.get<ScoutData>(`/scouting${queryString({ focus, max_age: maxAge, position })}`)
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : t('No se pudo consultar al ojeador.'), 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { void load() }, [focus, maxAge, position])

  return (
    <div className="stack mt-2">
      <Card>
        <div className="inline" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
          <div className="inline" style={{ alignItems: 'flex-start' }}>
            <span className="scout-avatar"><Compass size={20} /></span>
            <div>
              <div className="cat">{t('RED DE OJEADORES')}</div>
              <h3 style={{ margin: '3px 0' }}>{data?.scout.name || t('Consultando mercado…')}</h3>
              <p className="small muted" style={{ margin: 0 }}>{t('Recomendaciones ajustadas a tu presupuesto, nivel y carencias. La confianza depende del ojeador contratado.')}</p>
            </div>
          </div>
          <div className="inline"><Button size="sm" icon={Search} onClick={onUseMarket}>{t('Usar mercado completo')}</Button><Button size="sm" variant="ghost" icon={RefreshCw} onClick={load} loading={loading}>{t('Actualizar')}</Button></div>
        </div>

        <div className="form-row mt-2">
          <Field label={t('Enfoque del ojeador')}><select value={focus} onChange={(event) => setFocus(event.target.value)}>{(data?.focuses || []).map((item) => <option key={item.id} value={item.id}>{t(item.label)}</option>)}</select></Field>
          <Field label={t('Edad máxima')}><input value={maxAge} onChange={(event) => setMaxAge(event.target.value.replace(/\D/g, ''))} placeholder={t('Sin límite')} inputMode="numeric" /></Field>
          <Field label={t('Posición')}><select value={position} onChange={(event) => setPosition(event.target.value)}><option value="">{t('Todas')}</option>{['Portero', 'Central', 'Lateral', 'Medio', 'Delantero'].map((item) => <option key={item}>{item}</option>)}</select></Field>
          <Button variant="primary" icon={Sparkles} onClick={load}>{t('Recalcular')}</Button>
        </div>
      </Card>

      {loading ? <LoadingBlock label={t('Cruzando presupuesto, nivel y necesidades…')} /> : data ? (
        <>
          <div className="dashboard-kpis">
            <div className="stat-card"><span className="stat-top">{t('PRESUPUESTO')}</span><strong>{money(data.transfer_budget)}</strong><small>{t('Máximo para fichar')}</small></div>
            <div className="stat-card"><span className="stat-top">{t('NIVEL DEL EQUIPO')}</span><strong>{data.team_quality}</strong><small>{t('Media del once')}</small></div>
            <div className="stat-card"><span className="stat-top">{t('EDAD MEDIA')}</span><strong>{data.average_age}</strong><small>{t('Perfil de la plantilla')}</small></div>
            <div className="stat-card"><span className="stat-top">{t('CONFIANZA')}</span><strong>{data.scout.rating}/100</strong><small>{data.scout.confidence} · {data.scout.range}</small></div>
          </div>

          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">{t('NECESIDADES DETECTADAS')}</div><h3 style={{ margin: '3px 0 0' }}>{t('Dónde puede ayudar el mercado')}</h3></div><Badge tone="blue">{t('Ojeador {rating}/100', { rating: data.scout.rating })}</Badge></div>
            <div className="scout-needs mt-2">{data.needs.map((need) => <div className={`scout-need ${need.gap > 0 ? 'needs' : ''}`} key={need.group}><span>{t(need.group)} ({need.count}/{need.target})</span><b>{need.quality}</b>{need.gap > 0 && <small>{t('{count} refuerzo(s)', { count: need.gap })}</small>}</div>)}</div>
          </Card>

          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">{t('RECOMENDACIONES')}</div><h3 style={{ margin: '3px 0 0' }}>{t('{count} objetivos que encajan', { count: data.recommendations.length })}</h3></div><Badge tone="gold">Fit score</Badge></div>
            {data.recommendations.length ? (
              <div className="scout-list mt-2">
                {data.recommendations.map((row) => (
                  <button type="button" className="scout-card" key={row.player.id} onClick={() => navigate(`/game/player/${row.player.id}`)}>
                    <div className="scout-score"><b>{Math.round(row.score)}</b><span>fit</span></div>
                    <Avatar player={row.player} size={42} />
                    <div className="scout-card-main">
                      <div className="inline"><b>{row.player.name}</b>{row.player.transfer_listed && <Badge tone="gold">{t('En venta')}</Badge>}</div>
                      <span>{row.owner_name} · {row.league_name} · {t('{age} años · OVR', { age: row.age })} {row.overall.toFixed(1)}</span>
                      <div className="scout-reasons">{row.reasons.map((reason) => <Badge tone="neutral" key={reason}>{reason}</Badge>)}</div>
                    </div>
                    <div className="scout-card-side"><b>{money(row.asking)}</b><span>{t('salario {value}', { value: money(row.salary) })}</span><small>{row.affordable ? t('Dentro de presupuesto') : t('Fuera de presupuesto')}</small></div>
                    <ArrowRight size={15} className="muted" />
                  </button>
                ))}
              </div>
            ) : <EmptyState title={t('Sin objetivos que encajen')} body={t('El ojeador no encuentra perfiles que respeten tu presupuesto y nivel. Prueba otro enfoque o abre el mercado completo.')} action={<Button onClick={onUseMarket}>{t('Usar mercado completo')}</Button>} />}
          </Card>
        </>
      ) : <EmptyState title={t('No hay informe')} body={t('No se pudo generar la recomendación del ojeador.')} />}
    </div>
  )
}
