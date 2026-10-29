import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, CalendarDays, Play, Trophy } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { Fixture } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Crest, EmptyState, LoadingBlock, PageHeader } from '../components/ui'

interface CupPayload {
  status: string
  active: boolean
  round: number
  fixtures: Fixture[]
  next: Fixture | null
}

export default function CupPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<CupPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)

  function load() {
    setLoading(true)
    api.get<CupPayload>('/cup')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar la Copa.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function simulate(action: 'round' | 'all') {
    setBusy(action)
    try {
      const response = await api.post<{ state: unknown }>('/cup', { action })
      applyState(response.data.state as never)
      toast(response.message || 'Copa actualizada.', 'success')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo simular la Copa.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Cargando Copa del Rey…" />
  if (!data) return <Card><p className="muted">La Copa no está disponible para esta competición.</p><Button onClick={() => navigate('/game')}>Volver al club</Button></Card>

  return (
    <>
      <PageHeader
        eyebrow="Copa del Rey · DHA"
        title="La Copa del Rey"
        subtitle="Los ocho mejores de la primera vuelta. Cuartos, semifinal y final a partido único."
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button>}
      />
      <Card>
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">ESTADO</div><h2 style={{ margin: '3px 0' }}>{data.status}</h2><p className="small muted">Ronda {data.round || '—'} · {data.active ? 'En juego' : 'Pendiente o finalizada'}</p></div>
          <Trophy size={34} className="gold" />
        </div>
        {data.active && <div className="actions mt-2"><Button variant="primary" icon={Play} onClick={() => simulate('round')} loading={busy === 'round'}>Simular ronda</Button><Button icon={CalendarDays} onClick={() => simulate('all')} loading={busy === 'all'}>Simular resto</Button></div>}
        {!data.active && <p className="small muted mt-2">La Copa se activa tras la primera vuelta de la liga regular.</p>}
      </Card>

      {data.fixtures.length ? (
        <Card className="mt-2">
          <h3>Eliminatorias</h3>
          <div className="stack-sm">
            {data.fixtures.map((fixture) => (
              <div className="market-row" key={fixture.id}>
                <div className="market-row-main"><b>{fixture.home_name} vs {fixture.away_name}</b><span>{dateLabel(fixture.date)} · {fixture.label}</span></div>
                <Badge tone={fixture.played ? 'neutral' : 'warn'}>{fixture.played ? `${fixture.home_goals}-${fixture.away_goals}` : 'Pendiente'}</Badge>
              </div>
            ))}
          </div>
        </Card>
      ) : <EmptyState title="Sin eliminatorias" body="La Copa se sortea al final de la primera vuelta." />}
    </>
  )
}

