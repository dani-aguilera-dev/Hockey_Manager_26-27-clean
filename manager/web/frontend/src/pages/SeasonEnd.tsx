import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Trophy } from 'lucide-react'
import { api } from '../lib/api'
import type { SeasonSummary } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, LoadingBlock, PageHeader } from '../components/ui'

export default function SeasonEndPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [summary, setSummary] = useState<SeasonSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.get<{ summary: SeasonSummary }>('/season/end')
      .then(({ data }) => setSummary(data.summary))
      .catch((err) => toast(err instanceof Error ? err.message : 'La temporada sigue activa.', 'danger'))
      .finally(() => setLoading(false))
  }, [toast])

  async function nextSeason() {
    setBusy(true)
    try {
      const response = await api.post<{ state: unknown }>('/season/continue')
      applyState(response.data.state as never)
      toast(response.message || 'Nueva temporada.', 'success')
      navigate('/game')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo avanzar de temporada.', 'danger')
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <LoadingBlock label="Cerrando la temporada…" />
  if (!summary) return <Card><p className="muted">La temporada todavía no ha terminado.</p><Button onClick={() => navigate('/game')}>Volver al club</Button></Card>

  const promotion = summary.playout?.format === 'regional_promotion' ? (summary.playout as any) : null
  const promotionGroups = Array.isArray(promotion?.groups) ? promotion.groups : []
  const finalGroup = promotion?.final_group
  const promotedIds: string[] = Array.isArray(promotion?.promoted_ids) ? promotion.promoted_ids : []

  return (
    <>
      <PageHeader
        eyebrow="Fin de temporada"
        title={`Temporada ${summary.competition}`}
        subtitle={`Campeón: ${summary.champion || '—'} · tu posición: ${summary.user_position}º`}
        actions={<Button variant="primary" icon={ArrowRight} onClick={nextSeason} loading={busy}>Continuar siguiente temporada</Button>}
      />
      <div className="season-hero">
        <Trophy size={42} className="gold" />
        <div><h1>{summary.champion || 'Temporada completada'}</h1><p>Tu equipo terminó {summary.user_position}º en {summary.competition}. {summary.board_review ? `La junta ${summary.board_review.met ? 'da por cumplido' : 'no da por cumplido'} el objetivo.` : ''}</p></div>
        {summary.board_review && <Badge tone={summary.board_review.met ? 'ok' : 'danger'}>{summary.board_review.met ? 'Objetivo cumplido' : 'Objetivo no cumplido'}</Badge>}
      </div>

      <div className="season-grid">
        <Card>
          <h3>Clasificación final</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>#</th><th>Equipo</th><th className="num">PTS</th><th className="num">DG</th></tr></thead>
              <tbody>{summary.table.map((row) => <tr key={row.position}><td>{row.position}</td><td>{row.team}</td><td className="num">{row.points}</td><td className="num">{row.gd > 0 ? '+' : ''}{row.gd}</td></tr>)}</tbody>
            </table>
          </div>
        </Card>
        <Card>
          <h3>Junta y movimientos</h3>
          {summary.board_review && <><p className="small">Objetivo {summary.board_review.target}º · posición {summary.board_review.position}º</p><p className="small">Confianza {summary.board_review.confidence_before} → {summary.board_review.confidence_after}/100</p><p className="small muted">{summary.board_review.message}</p></>}
          <p className="small"><b>Ascensos:</b> {summary.promoted?.join(', ') || '—'}</p>
          <p className="small"><b>Descensos:</b> {summary.relegated?.join(', ') || '—'}</p>
          {promotion && (
            <div className="notice notice-info mt-2">
              <div>
                <b>Fase Nacional de ascenso a DHB</b>
                <p className="small">Cuatro grupos geográficos · liguilla a partido único · los dos primeros de la fase final ascienden.</p>
                <div className="promotion-groups">
                  {promotionGroups.map((group: any) => (
                    <div className="promotion-group" key={group.name}>
                      <div className="inline" style={{ justifyContent: 'space-between' }}>
                        <b>{group.name}</b>
                        <Badge tone="gold">{group.winner || '—'}</Badge>
                      </div>
                      <div className="table-wrap">
                        <table className="data-table">
                          <thead><tr><th>#</th><th>Equipo</th><th className="num">PTS</th><th className="num">DG</th></tr></thead>
                          <tbody>{(group.table || []).map((row: any) => (
                            <tr key={row.team_id}>
                              <td>{row.position}</td>
                              <td>{row.team}</td>
                              <td className="num">{row.points}</td>
                              <td className="num">{row.gd > 0 ? '+' : ''}{row.gd}</td>
                            </tr>
                          ))}</tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
                {finalGroup && (
                  <div className="promotion-final mt-2">
                    <div className="inline" style={{ justifyContent: 'space-between' }}>
                      <b>Fase final</b>
                      <Badge tone="ok">2 plazas de ascenso</Badge>
                    </div>
                    <div className="table-wrap">
                      <table className="data-table">
                        <thead><tr><th>#</th><th>Equipo</th><th className="num">PTS</th><th className="num">DG</th><th /></tr></thead>
                        <tbody>{(finalGroup.table || []).map((row: any) => (
                          <tr key={row.team_id}>
                            <td>{row.position}</td>
                            <td>{row.team}</td>
                            <td className="num">{row.points}</td>
                            <td className="num">{row.gd > 0 ? '+' : ''}{row.gd}</td>
                            <td>{promotedIds.includes(row.team_id) ? <Badge tone="ok">Asciende</Badge> : null}</td>
                          </tr>
                        ))}</tbody>
                      </table>
                    </div>
                  </div>
                )}
                <p className="small"><b>Ascendidos:</b> {summary.promoted?.join(', ') || '—'}</p>
              </div>
            </div>
          )}
          {summary.cup_winner && <p className="small"><b>Copa:</b> {summary.cup_winner}{summary.cup_third ? ` · tercero ${summary.cup_third}` : ''}</p>}
          {summary.ehl_winner && <p className="small"><b>EHL:</b> {summary.ehl_winner}</p>}
          {summary.retirements?.length > 0 && <><p className="small"><b>Retiros:</b> {summary.retirements.length}</p>{summary.retirements.slice(0, 6).map((retirement) => <p className="small muted" key={`${retirement.player}-${retirement.club}`}>{retirement.player} · {retirement.club} · {retirement.age} años</p>)}</>}
        </Card>
      </div>
    </>
  )
}
