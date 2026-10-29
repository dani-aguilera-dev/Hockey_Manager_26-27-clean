import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Compass, RefreshCw, Search, Sparkles } from 'lucide-react'
import { api, queryString } from '../lib/api'
import { money } from '../lib/format'
import type { ScoutData } from '../types'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, EmptyState, Field, LoadingBlock } from '../components/ui'

export default function ScoutPanel({ onUseMarket }: { onUseMarket: () => void }) {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [data, setData] = useState<ScoutData | null>(null)
  const [loading, setLoading] = useState(true)
  const [focus, setFocus] = useState('equilibrado')
  const [maxAge, setMaxAge] = useState('')
  const [position, setPosition] = useState('')

  function load() {
    setLoading(true)
    api.get<ScoutData>(`/scouting${queryString({ focus, max_age: maxAge, position })}`)
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo consultar al ojeador.', 'danger'))
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
              <div className="cat">RED DE OJEADORES</div>
              <h3 style={{ margin: '3px 0' }}>{data?.scout.name || 'Consultando mercado…'}</h3>
              <p className="small muted" style={{ margin: 0 }}>Recomendaciones ajustadas a tu presupuesto, nivel y carencias. La confianza depende del ojeador contratado.</p>
            </div>
          </div>
          <div className="inline"><Button size="sm" icon={Search} onClick={onUseMarket}>Usar mercado completo</Button><Button size="sm" variant="ghost" icon={RefreshCw} onClick={load} loading={loading}>Actualizar</Button></div>
        </div>

        <div className="form-row mt-2">
          <Field label="Enfoque del ojeador"><select value={focus} onChange={(event) => setFocus(event.target.value)}>{(data?.focuses || []).map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></Field>
          <Field label="Edad máxima"><input value={maxAge} onChange={(event) => setMaxAge(event.target.value.replace(/\D/g, ''))} placeholder="Sin límite" inputMode="numeric" /></Field>
          <Field label="Posición"><select value={position} onChange={(event) => setPosition(event.target.value)}><option value="">Todas</option>{['Portero', 'Central', 'Lateral', 'Medio', 'Delantero'].map((item) => <option key={item}>{item}</option>)}</select></Field>
          <Button variant="primary" icon={Sparkles} onClick={load}>Recalcular</Button>
        </div>
      </Card>

      {loading ? <LoadingBlock label="Cruzando presupuesto, nivel y necesidades…" /> : data ? (
        <>
          <div className="dashboard-kpis">
            <div className="stat-card"><span className="stat-top">PRESUPUESTO</span><strong>{money(data.transfer_budget)}</strong><small>Máximo para fichar</small></div>
            <div className="stat-card"><span className="stat-top">NIVEL DEL EQUIPO</span><strong>{data.team_quality}</strong><small>Media del once</small></div>
            <div className="stat-card"><span className="stat-top">EDAD MEDIA</span><strong>{data.average_age}</strong><small>Perfil de la plantilla</small></div>
            <div className="stat-card"><span className="stat-top">CONFIANZA</span><strong>{data.scout.rating}/100</strong><small>{data.scout.confidence} · {data.scout.range}</small></div>
          </div>

          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">NECESIDADES DETECTADAS</div><h3 style={{ margin: '3px 0 0' }}>Dónde puede ayudar el mercado</h3></div><Badge tone="blue">Ojeador {data.scout.rating}/100</Badge></div>
            <div className="scout-needs mt-2">{data.needs.map((need) => <div className={`scout-need ${need.gap > 0 ? 'needs' : ''}`} key={need.group}><span>{need.label}</span><b>{need.quality}</b>{need.gap > 0 && <small>{need.gap} refuerzo(s)</small>}</div>)}</div>
          </Card>

          <Card>
            <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">RECOMENDACIONES</div><h3 style={{ margin: '3px 0 0' }}>{data.recommendations.length} objetivos que encajan</h3></div><Badge tone="gold">Fit score</Badge></div>
            {data.recommendations.length ? (
              <div className="scout-list mt-2">
                {data.recommendations.map((row) => (
                  <button type="button" className="scout-card" key={row.player.id} onClick={() => navigate(`/game/player/${row.player.id}`)}>
                    <div className="scout-score"><b>{Math.round(row.score)}</b><span>fit</span></div>
                    <Avatar player={row.player} size={42} />
                    <div className="scout-card-main">
                      <div className="inline"><b>{row.player.name}</b>{row.player.transfer_listed && <Badge tone="gold">En venta</Badge>}</div>
                      <span>{row.owner_name} · {row.league_name} · {row.age} años · OVR {row.overall.toFixed(1)}</span>
                      <div className="scout-reasons">{row.reasons.map((reason) => <Badge tone="neutral" key={reason}>{reason}</Badge>)}</div>
                    </div>
                    <div className="scout-card-side"><b>{money(row.asking)}</b><span>salario {money(row.salary)}</span><small>{row.affordable ? 'Dentro de presupuesto' : 'Fuera de presupuesto'}</small></div>
                    <ArrowRight size={15} className="muted" />
                  </button>
                ))}
              </div>
            ) : <EmptyState title="Sin objetivos que encajen" body="El ojeador no encuentra perfiles que respeten tu presupuesto y nivel. Prueba otro enfoque o abre el mercado completo." action={<Button onClick={onUseMarket}>Usar mercado completo</Button>} />}
          </Card>
        </>
      ) : <EmptyState title="No hay informe" body="No se pudo generar la recomendación del ojeador." />}
    </div>
  )
}
