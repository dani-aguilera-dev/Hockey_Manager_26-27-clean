import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Play, Trophy } from 'lucide-react'
import { api } from '../lib/api'
import type { EhlData } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, EmptyState, LoadingBlock, PageHeader } from '../components/ui'

interface EhlPayload {
  ehl: EhlData
  next: string
  status: string
}

export default function EhlPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<EhlPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  function load() {
    setLoading(true)
    api.get<EhlPayload>('/ehl')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la EHL.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function simulate() {
    setBusy(true)
    try {
      const response = await api.post<{ state: unknown; ehl: EhlData; status: string }>('/ehl')
      applyState(response.data.state as never)
      setData((current) => current ? { ...current, ehl: response.data.ehl, status: response.data.status } : current)
      toast(response.message || 'Ronda de EHL simulada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo simular la EHL.', 'danger')
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <LoadingBlock label="Cargando EHL…" />
  if (!data) return <Card><p className="muted">La EHL no está disponible para esta competición.</p><Button onClick={() => navigate('/game')}>Volver al club</Button></Card>

  const ehl = data.ehl || {}
  return (
    <>
      <PageHeader
        eyebrow="Europa · Euro Hockey League"
        title="La EHL"
        subtitle="Torneo europeo simplificado de final a ocho. Tres clubes españoles y cinco europeos."
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button>}
      />
      <Card>
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">ESTADO</div><h2 style={{ margin: '3px 0' }}>{data.status}</h2><p className="small muted">{ehl.active ? `Ronda ${ehl.round || 1} · ${data.next ? `Próxima fecha ${data.next}` : ''}` : 'Competición finalizada'}</p></div>
          <Trophy size={34} className="gold" />
        </div>
        {ehl.active && <Button variant="primary" className="mt-2" icon={Play} onClick={simulate} loading={busy}>Simular ronda</Button>}
        {ehl.winner_name && <p className="small muted mt-2">Campeón: <b className="gold">{ehl.winner_name}</b></p>}
      </Card>

      <Card className="mt-2">
        <h3>Participantes</h3>
        <div className="inline">{ehl.participants?.map((name) => <Badge key={name} tone="neutral">{name}</Badge>) || <span className="small muted">Pendiente de clasificación.</span>}</div>
      </Card>

      {ehl.fixtures?.length ? (
        <Card className="mt-2">
          <h3>Eliminatorias</h3>
          <div className="stack-sm">
            {ehl.fixtures.map((fixture, index) => (
              <div className="market-row" key={`${fixture.home.id}-${index}`}>
                <div className="market-row-main"><b>{fixture.home.name} vs {fixture.away.name}</b><span>{fixture.home.country} · {fixture.away.country}</span></div>
                <Badge tone={fixture.played ? 'neutral' : 'warn'}>{fixture.played ? `${fixture.home_goals}-${fixture.away_goals}` : 'Pendiente'}</Badge>
              </div>
            ))}
          </div>
        </Card>
      ) : <EmptyState title="Sin eliminatorias" body="La EHL se activa cuando el club se clasifica." />}

      {ehl.results?.length ? (
        <Card className="mt-2">
          <h3>Resultados</h3>
          {ehl.results.slice().reverse().map((round) => (
            <div key={`${round.round}-${round.label}`} className="mt-2"><div className="cat">{round.label}</div>{round.fixtures.map((fixture, index) => <p className="small" key={index}>{fixture.home} {fixture.home_goals}-{fixture.away_goals} {fixture.away}</p>)}</div>
          ))}
        </Card>
      ) : null}
    </>
  )
}
