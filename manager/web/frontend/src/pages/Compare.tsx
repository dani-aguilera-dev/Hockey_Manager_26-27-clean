import { useEffect, useState } from 'react'
import { ArrowLeftRight, BarChart3, Shield, Star, UserRound } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { CompareCandidate, CompareData } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Field, LoadingBlock, PageHeader, StatCard } from '../components/ui'

function valueTone(value: number) {
  if (value >= 80) return 'ok'
  if (value >= 60) return 'gold'
  return 'neutral'
}

export default function ComparePage() {
  const { toast } = useToast()
  const [candidates, setCandidates] = useState<CompareCandidate[]>([])
  const [playerA, setPlayerA] = useState('')
  const [playerB, setPlayerB] = useState('')
  const [data, setData] = useState<CompareData | null>(null)
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')

  function loadCandidates(search = '') {
    api.get<{ players: CompareCandidate[] }>(`/compare/players?q=${encodeURIComponent(search)}`)
      .then(({ data }) => {
        setCandidates(data.players)
        setPlayerA((current) => current || data.players[0]?.id || '')
        setPlayerB((current) => current || data.players[1]?.id || '')
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar los jugadores.', 'danger'))
  }

  useEffect(() => { loadCandidates() }, [])

  useEffect(() => {
    if (!playerA || !playerB || playerA === playerB) {
      setData(null)
      setLoading(false)
      return
    }
    setLoading(true)
    api.get<CompareData>(`/compare?player_a=${encodeURIComponent(playerA)}&player_b=${encodeURIComponent(playerB)}`)
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo comparar.', 'danger'))
      .finally(() => setLoading(false))
  }, [playerA, playerB, toast])

  if (loading && !data) return <LoadingBlock label="Comparando fichas…" />
  if (!data) {
    return (
      <>
        <PageHeader eyebrow="Mercado · análisis · decisiones" title="Comparar jugadores" subtitle="Selecciona dos jugadores para comparar atributos, estadísticas y contrato." />
        <Card>
          <div className="compare-selectors">
            <Field label="Jugador A"><select value={playerA} onChange={(event) => setPlayerA(event.target.value)} data-testid="compare-player-a">{candidates.map((player) => <option key={player.id} value={player.id}>{player.name} · {player.team_name}</option>)}</select></Field>
            <Field label="Jugador B"><select value={playerB} onChange={(event) => setPlayerB(event.target.value)} data-testid="compare-player-b">{candidates.map((player) => <option key={player.id} value={player.id}>{player.name} · {player.team_name}</option>)}</select></Field>
          </div>
          <p className="small muted mt-2">Selecciona dos jugadores distintos. Los atributos y estadísticas salen de la partida.</p>
        </Card>
      </>
    )
  }

  const { a, b, summary, differences } = data
  return (
    <>
      <PageHeader
        eyebrow="Mercado · análisis · decisiones"
        title="Comparar jugadores"
        subtitle={`${a.name} frente a ${b.name}. Atributos, rendimiento y contrato lado a lado.`}
        actions={<Badge tone={summary.winner === 'a' ? 'ok' : summary.winner === 'b' ? 'gold' : 'neutral'}>{summary.winner === 'a' ? `${a.name} gana ${summary.a_wins}-${summary.b_wins}` : summary.winner === 'b' ? `${b.name} gana ${summary.b_wins}-${summary.a_wins}` : `Empate ${summary.a_wins}-${summary.b_wins}`}</Badge>}
      />

      <Card className="mt-2">
        <div className="compare-selectors">
          <Field label="Jugador A"><select value={playerA} onChange={(event) => setPlayerA(event.target.value)} data-testid="compare-player-a">{candidates.map((player) => <option key={player.id} value={player.id}>{player.name} · {player.team_name}</option>)}</select></Field>
          <Field label="Jugador B"><select value={playerB} onChange={(event) => setPlayerB(event.target.value)} data-testid="compare-player-b">{candidates.map((player) => <option key={player.id} value={player.id}>{player.name} · {player.team_name}</option>)}</select></Field>
          <Field label="Buscar jugador"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nombre o club…" onKeyDown={(event) => { if (event.key === 'Enter') loadCandidates(query) }} /></Field>
          <Button icon={ArrowLeftRight} onClick={() => loadCandidates(query)}>Buscar</Button>
        </div>
      </Card>

      <div className="compare-hero mt-2">
        <div className="compare-player-card">
          <Badge tone={valueTone(a.overall)}>{a.overall} OVR</Badge>
          <h2>{a.name}</h2>
          <p>{a.team_name} · {a.league_name} · {a.position} · {a.age} años</p>
          <div className="compare-player-numbers"><span>Potencial <b>{a.potential}</b></span><span>Valor <b>{money(a.value)}</b></span><span>Salario <b>{money(a.salary)}</b></span><span>Contrato <b>{a.contract_until}</b></span></div>
          <div className="compare-stats"><span>{a.apps} PJ</span><span>{a.goals} G</span><span>{a.assists} A</span><span>Rating {a.rating}</span></div>
        </div>
        <div className="compare-vs"><ArrowLeftRight size={22} /><span>VS</span></div>
        <div className="compare-player-card">
          <Badge tone={valueTone(b.overall)}>{b.overall} OVR</Badge>
          <h2>{b.name}</h2>
          <p>{b.team_name} · {b.league_name} · {b.position} · {b.age} años</p>
          <div className="compare-player-numbers"><span>Potencial <b>{b.potential}</b></span><span>Valor <b>{money(b.value)}</b></span><span>Salario <b>{money(b.salary)}</b></span><span>Contrato <b>{b.contract_until}</b></span></div>
          <div className="compare-stats"><span>{b.apps} PJ</span><span>{b.goals} G</span><span>{b.assists} A</span><span>Rating {b.rating}</span></div>
        </div>
      </div>

      <div className="dashboard-kpis mt-2">
        <StatCard label="Atributos ganados" value={`${summary.a_wins} - ${summary.b_wins}`} hint={`${summary.ties} empates`} tone="blue" icon={BarChart3} />
        <StatCard label="Diferencia OVR" value={differences.overall >= 0 ? `+${differences.overall}` : differences.overall} hint={`Potencial ${differences.potential >= 0 ? '+' : ''}${differences.potential}`} tone="gold" icon={Star} />
        <StatCard label="Diferencia de valor" value={money(differences.value)} hint={`Salario ${money(differences.salary)}`} icon={Shield} />
        <StatCard label="Edad" value={`${a.age} / ${b.age}`} hint={`Diferencia ${differences.age}`} icon={UserRound} />
      </div>

      <Card className="mt-2 compare-grid">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">ATRIBUTOS</div><h3 style={{ margin: '3px 0 0' }}>Comparación detallada</h3></div>
          <Badge tone="neutral">{summary.attributes}</Badge>
        </div>
        {data.categories.map((category) => (
          <div className="compare-category" key={category.name}>
            <div className="compare-category-title">{category.name}</div>
            {category.rows.map((row) => (
              <div className={`compare-row ${row.winner}`} key={row.key}>
                <b>{row.a}</b>
                <div className="compare-attribute">
                  <span>{row.label}</span>
                  <div className="compare-bars">
                    <i style={{ width: `${row.a}%` }} className="compare-bar-a" />
                    <i style={{ width: `${row.b}%` }} className="compare-bar-b" />
                  </div>
                </div>
                <b>{row.b}</b>
              </div>
            ))}
          </div>
        ))}
      </Card>
    </>
  )
}
