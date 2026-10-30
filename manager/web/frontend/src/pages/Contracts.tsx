import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CalendarClock, FileSignature, ShieldCheck, Wallet } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { ContractPlayer, ContractsData } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader, StatCard } from '../components/ui'

type Filter = 'all' | 'expira' | 'renovar' | 'seguro' | 'cedido'

const statusLabels: Record<string, string> = {
  expira: 'Expira',
  renovar: 'Renovar',
  seguro: 'Seguro',
  cedido: 'Cedido',
}

const statusTones: Record<string, 'ok' | 'warn' | 'danger' | 'neutral'> = {
  expira: 'danger',
  renovar: 'warn',
  seguro: 'ok',
  cedido: 'neutral',
}

export default function ContractsPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [data, setData] = useState<ContractsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<Filter>('all')

  function load() {
    setLoading(true)
    api.get<ContractsData>('/contracts')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar los contratos.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading && !data) return <LoadingBlock label="Revisando contratos y vencimientos…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar los contratos.</p></Card>

  const rows = filter === 'all' ? data.players : data.players.filter((player) => player.status === filter)
  return (
    <>
      <PageHeader
        eyebrow="Dirección deportiva · contratos · salarios"
        title="Centro de contratos"
        subtitle="Controla vencimientos, años restantes, salarios y masa salarial. Renueva antes de que el mercado se adelante."
        actions={<><Badge tone="gold">{data.summary.expiring + data.summary.renewal} por resolver</Badge><Button icon={CalendarClock} onClick={load}>Actualizar</Button></>}
      />

      <div className="dashboard-kpis">
        <StatCard label="Jugadores" value={data.summary.players} hint="Fichas senior" tone="blue" icon={ShieldCheck} />
        <StatCard label="Masa salarial" value={money(data.summary.wage_bill)} hint={`Media ${money(data.summary.average_salary)}`} tone="danger" icon={Wallet} />
        <StatCard label="Expiran" value={data.summary.expiring} hint={`${data.summary.renewal} en año de renovación`} tone="gold" icon={CalendarClock} />
        <StatCard label="Caja" value={money(data.summary.budget)} hint={`Presupuesto salarial ${money(data.summary.wage_budget)}`} />
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><div><div className="cat">VENCIMIENTOS</div><h3 style={{ margin: '3px 0 0' }}>Prioridades de renovación</h3></div><Badge tone="warn">{data.renewal_candidates.length}</Badge></div>
          <div className="stack-sm mt-2">
            {data.renewal_candidates.map((player) => (
              <div className="contract-row" key={player.id}>
                <div><b>{player.name}</b><span>{player.position} · {player.age} años · {player.contract_until}</span></div>
                <Badge tone={statusTones[player.status]}>{statusLabels[player.status]}</Badge>
                <b>{money(player.salary)}</b>
                <Button size="sm" variant="ghost" icon={FileSignature} onClick={() => navigate('/game/market/renew')}>Renovar</Button>
              </div>
            ))}
            {!data.renewal_candidates.length && <p className="small muted">No hay contratos urgentes.</p>}
          </div>
        </Card>
        <Card>
          <h3>Mayores salarios</h3>
          <div className="stack-sm mt-2">
            {data.top_earners.map((player) => (
              <div className="contract-row" key={player.id}><div><b>{player.name}</b><span>{player.position} · {player.contract_until}</span></div><b>{money(player.salary)}</b></div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">PLANTILLA</div><h3 style={{ margin: '3px 0 0' }}>Situación contractual</h3></div>
          <div className="actions">
            {(['all', 'expira', 'renovar', 'seguro', 'cedido'] as Filter[]).map((value) => <Button key={value} size="sm" variant={filter === value ? 'primary' : 'ghost'} onClick={() => setFilter(value)}>{value === 'all' ? 'Todos' : statusLabels[value]}</Button>)}
          </div>
        </div>
        <div className="table-wrap mt-2">
          <table className="data-table">
            <thead><tr><th>Jugador</th><th>Pos</th><th className="num">Edad</th><th className="num">OVR</th><th className="num">Salario</th><th>Contrato</th><th className="num">Años</th><th>Estado</th><th></th></tr></thead>
            <tbody>{rows.map((player) => (
              <tr key={player.id}>
                <td>{player.name}</td><td>{player.position}</td><td className="num">{player.age}</td><td className="num">{player.overall}</td><td className="num">{money(player.salary)}</td><td>{player.contract_until}</td><td className="num">{player.years_remaining}</td><td><Badge tone={statusTones[player.status]}>{statusLabels[player.status]}</Badge></td><td><Button size="sm" variant="ghost" onClick={() => navigate(`/game/player/${player.id}`)}>Ficha</Button></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
