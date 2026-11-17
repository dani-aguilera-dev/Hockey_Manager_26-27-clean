import { useEffect, useState } from 'react'
import { BadgeEuro, Banknote, Save, TrendingDown, TrendingUp, Wallet } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { FinanceOverview } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../lib/i18n'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

export default function FinancePage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [data, setData] = useState<FinanceOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [ticketPrice, setTicketPrice] = useState('15')
  const [saved, setSaved] = useState(false)

  function load() {
    setLoading(true)
    api.get<FinanceOverview>('/finance')
      .then(({ data }) => {
        setData(data)
        setTicketPrice(String(data.ticket_price ?? 15))
        setSaved(false)
      })
      .catch((err) => toast(err instanceof Error ? err.message : t('No se pudieron cargar las finanzas.'), 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function saveTicket() {
    setBusy(true)
    try {
      const response = await api.post<{ finance: FinanceOverview; state: unknown }>('/finance/ticket', { price: Number(ticketPrice) })
      setData(response.data.finance)
      applyState(response.data.state as never)
      setSaved(true)
      toast(response.message || t('Precio de entrada actualizado.'), 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo actualizar la taquilla.'), 'danger')
    } finally {
      setBusy(false)
    }
  }

  if (loading && !data) return <LoadingBlock label={t('Cuadrando las cuentas…')} />
  if (!data) return <Card><p className="muted">{t('No se pudieron cargar las finanzas.')}</p></Card>

  const annualPositive = data.annual_net >= 0
  return (
    <>
      <PageHeader
        eyebrow={t('Dirección financiera · masa salarial · taquilla')}
        title={t('Centro financiero')}
        subtitle={t('Caja, presupuesto, salarios, patrocinios, taquilla y proyección anual. Toma decisiones con la cuenta de resultados delante.')}
        actions={<>{saved && <Badge tone="ok" className="finance-saved">{t('Guardado')}</Badge>}<Badge tone={data.wage_ratio > 100 ? 'danger' : 'ok'}>{t('{value}% salarios/ingresos', { value: data.wage_ratio })}</Badge></>}
      />

      <div className="dashboard-kpis">
        <StatCard label={t('Caja disponible')} value={money(data.cash)} hint={t('Tesorería del club')} tone="gold" icon={Wallet} />
        <StatCard label={t('Presupuesto de fichajes')} value={money(data.transfer_budget)} hint={t('Disponible para incorporaciones')} tone="blue" icon={Banknote} />
        <StatCard label={t('Masa salarial anual')} value={money(data.annual_wage_bill)} hint={t('{value} por jornada', { value: money(data.round_player_wages + data.round_staff_wages) })} tone="danger" icon={TrendingDown} />
        <StatCard label={t('Neto anual')} value={money(data.annual_net)} hint={t('Ingresos {value}', { value: money(data.annual_income) })} tone={annualPositive ? 'ok' : 'danger'} icon={annualPositive ? TrendingUp : TrendingDown} />
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">{t('CUENTA DE RESULTADOS')}</div><h3 style={{ margin: '3px 0 0' }}>{t('Ingresos y gastos')}</h3></div><BadgeEuro size={20} className="gold" /></div>
          <div className="finance-breakdown mt-2">
            <div><span>{t('Taquilla acumulada')}</span><b>{money(data.gate)}</b></div>
            <div><span>{t('Patrocinio acumulado')}</span><b>{money(data.sponsor)}</b></div>
            <div><span>{t('Salarios de jugadores')}</span><b className="danger">−{money(data.player_wages)}</b></div>
            <div><span>{t('Salarios de staff')}</span><b className="danger">−{money(data.staff_wages)}</b></div>
            <div><span>{t('Viajes')}</span><b className="danger">−{money(data.travel)}</b></div>
            <div className="finance-total"><span>{t('Neto acumulado')}</span><b className={data.net >= 0 ? 'gold' : 'danger'}>{money(data.net)}</b></div>
          </div>
        </Card>
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">{t('SOSTENIBILIDAD')}</div><h3 style={{ margin: '3px 0 0' }}>{t('Proyección anual')}</h3></div><Badge tone={annualPositive ? 'ok' : 'danger'}>{annualPositive ? t('Superávit') : t('Déficit')}</Badge></div>
          <div className="stack-sm mt-2">
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Ingresos anuales')}</span><b>{money(data.annual_income)}</b></div><Progress value={100} tone="ok" /></div>
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Gastos anuales')}</span><b>{money(data.annual_expenses)}</b></div><Progress value={Math.min(100, data.wage_ratio)} tone={data.wage_ratio > 100 ? 'danger' : 'gold'} /></div>
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Ratio salarios/ingresos')}</span><b>{data.wage_ratio}%</b></div></div>
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">{t('Jornadas de caja')}</span><b>{data.runway_rounds >= 99 ? t('Sin burn') : `${data.runway_rounds}`}</b></div></div>
            <p className="small muted">{t('Un ratio por encima del 100% obliga a vender, recortar salarios o aumentar ingresos comerciales.')}</p>
          </div>
        </Card>
      </div>

      <div className="split-2 mt-2">
        <Card>
          <h3>{t('Mayores salarios')}</h3>
          <div className="table-wrap mt-2">
            <table className="data-table">
              <thead><tr><th>{t('Jugador')}</th><th>{t('Pos')}</th><th className="num">{t('OVR')}</th><th className="num">{t('Salario')}</th><th className="num">{t('% masa')}</th></tr></thead>
              <tbody>{data.top_earners.map((player) => <tr key={player.id}><td>{player.name}</td><td>{player.position}</td><td className="num">{player.overall}</td><td className="num">{money(player.salary)}</td><td className="num">{player.share}%</td></tr>)}</tbody>
            </table>
          </div>
        </Card>
        <Card>
          <h3>{t('Staff')}</h3>
          <div className="stack-sm mt-2">
            {data.staff_wage_rows.map((member) => <div className="finance-row" key={`${member.role}-${member.name}`}><span>{member.name}<small>{member.role}</small></span><b>{money(member.salary)}</b></div>)}
            {!data.staff_wage_rows.length && <p className="small muted">{t('Sin staff contratado.')}</p>}
          </div>
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">{t('TAQUILLA')}</div><h3 style={{ margin: '3px 0 0' }}>{t('Precio de entrada y escenarios')}</h3></div><Badge tone="blue">{t('{value} € actual', { value: data.ticket_price ?? 15 })}</Badge></div>
        <div className="finance-ticket-form mt-2">
          <Field label={t('Nuevo precio')}><input type="number" min={8} max={40} value={ticketPrice} onChange={(event) => setTicketPrice(event.target.value)} data-testid="finance-ticket-input" /></Field>
          <Button variant="primary" icon={Save} onClick={saveTicket} loading={busy} data-testid="finance-ticket-save">{t('Guardar precio')}</Button>
        </div>
        <div className="table-wrap mt-2">
          <table className="data-table">
            <thead><tr><th>{t('Precio')}</th><th className="num">{t('Asistencia estimada')}</th><th className="num">{t('Ingreso por partido')}</th><th className="num">{t('Temporada')}</th></tr></thead>
            <tbody>{data.ticket_scenarios.map((scenario) => <tr key={scenario.price} className={scenario.price === data.ticket_price ? 'selected-row' : ''}><td>{scenario.price} €</td><td className="num">{scenario.attendance}</td><td className="num">{money(scenario.revenue)}</td><td className="num">{money(scenario.season_revenue)}</td></tr>)}</tbody>
          </table>
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <h3>{t('Historial de jornadas')}</h3>
          <div className="table-wrap mt-2">
            <table className="data-table">
              <thead><tr><th>{t('J')}</th><th className="num">{t('Taquilla')}</th><th className="num">{t('Patrocinio')}</th><th className="num">{t('Salarios')}</th><th className="num">{t('Neto')}</th><th className="num">{t('Caja')}</th></tr></thead>
              <tbody>{data.log.map((entry) => <tr key={entry.round}><td>{entry.round}</td><td className="num">{money(entry.gate)}</td><td className="num">{money(entry.sponsor)}</td><td className="num">−{money(entry.wages)}</td><td className={`num ${entry.net >= 0 ? 'gold' : 'danger'}`}>{money(entry.net)}</td><td className="num">{money(entry.cash_after)}</td></tr>)}</tbody>
            </table>
          </div>
          {!data.log.length && <p className="small muted mt-2">{t('Las cuentas aparecerán tras la primera jornada.')}</p>}
        </Card>
        <Card>
          <h3>{t('Acuerdos activos')}</h3>
          <div className="stack-sm mt-2">
            {data.active_sponsors.map((deal) => <div className="finance-row" key={deal.id}><span>{deal.name}<small>{t(deal.category)} · {t('hasta {date}', { date: deal.end || '—' })}</small></span><b>{money(deal.annual)}</b></div>)}
            {data.equipment_deals.map((deal) => <div className="finance-row" key={deal.id}><span>{deal.brand}<small>{t('Equipación · hasta {date}', { date: deal.end || '—' })}</small></span><b>{money(deal.annual)}</b></div>)}
            {!data.active_sponsors.length && !data.equipment_deals.length && <p className="small muted">{t('Sin patrocinios ni marcas de equipación activas.')}</p>}
          </div>
        </Card>
      </div>
    </>
  )
}
