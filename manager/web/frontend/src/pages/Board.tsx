import { useEffect, useState } from 'react'
import { ArrowUpRight, Landmark, ShieldCheck, TrendingUp, Users, Wallet } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, money } from '../lib/format'
import type { BoardData, BoardRequestOption } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../lib/i18n'
import { Badge, Button, Card, LoadingBlock, PageHeader, Progress, StatCard } from '../components/ui'

export default function BoardPage() {
  const { applyState } = useGame()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [data, setData] = useState<BoardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)

  function load() {
    setLoading(true)
    api.get<BoardData>('/board')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : t('No se pudo cargar la junta.'), 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function makeRequest(request: BoardRequestOption) {
    setBusy(request.id)
    try {
      const response = await api.post<{ board: BoardData; state: unknown }>('/board/request', { request_id: request.id })
      setData(response.data.board)
      applyState(response.data.state as never)
      toast(response.message || t('Petición registrada.'), response.data.board.history[0]?.approved ? 'success' : 'info')
    } catch (err) {
      toast(err instanceof Error ? err.message : t('No se pudo procesar la petición.'), 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label={t('Reuniéndose con la junta…')} />
  if (!data) return <Card><p className="muted">{t('No se pudo cargar la junta.')}</p></Card>

  const confidenceTone = data.confidence >= 65 ? 'ok' : data.confidence >= 40 ? 'gold' : 'danger'

  return (
    <>
      <PageHeader
        eyebrow={`${data.competition.short_name} · ${data.competition.position}º de ${data.competition.teams}`}
        title={t('Junta y visión de club')}
        subtitle={t('Confianza, objetivos a medio plazo, instalaciones y peticiones de inversión. La junta decide según resultados, caja y proyecto.')}
        actions={<Badge tone={confidenceTone}>{t('{value}/100 confianza', { value: data.confidence })}</Badge>}
      />

      <div className="dashboard-kpis">
        <StatCard label={t('Confianza de la junta')} value={`${data.confidence}/100`} hint={t('Presión {pressure} · paciencia {patience}/5', { pressure: t(data.pressure), patience: data.patience })} tone={confidenceTone} icon={Landmark} />
        <StatCard label={t('Afición')} value={`${data.fan_confidence}/100`} hint={t('Apoyo de la grada')} tone="blue" icon={Users} />
        <StatCard label={t('Caja disponible')} value={money(data.budget)} hint={t('Fichajes {value}', { value: money(data.transfer_budget) })} tone="gold" icon={Wallet} />
        <StatCard label={t('Posición')} value={`${data.competition.position}º`} hint={t('{competition} · {count} equipos', { competition: data.competition.short_name, count: data.competition.teams })} icon={TrendingUp} />
      </div>

      <div className="split-2 mt-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">{t('VISIÓN DE CLUB')}</div><h3 style={{ margin: '3px 0 0' }}>{t('El proyecto que defiende la junta')}</h3></div>
            <ShieldCheck size={22} className="gold" />
          </div>
          <div className="stack-sm mt-2">
            {data.vision.map((item) => (
              <div className="board-vision-row" key={item.horizon}>
                <Badge tone="neutral">{t(item.horizon)}</Badge>
                <div><b>{t(item.goal)}</b><span>{item.detail.startsWith('Objetivo de la temporada en ') ? t('Objetivo de la temporada en {league}', { league: item.detail.replace('Objetivo de la temporada en ', '') }) : t(item.detail)}</span></div>
              </div>
            ))}
          </div>
          <p className="small muted mt-2">{t('Objetivo oficial: {value}.', { value: data.expectation || t('Consolidar el proyecto') })}</p>
        </Card>

        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <div><div className="cat">{t('INSTALACIONES')}</div><h3 style={{ margin: '3px 0 0' }}>{data.stadium.name || t('Instalaciones del club')}</h3></div>
            <Badge tone="neutral">{t('{value} plazas', { value: data.stadium.capacity.toLocaleString('es-ES') })}</Badge>
          </div>
          <div className="board-facilities mt-2">
            {data.facilities.map((facility) => (
              <div className="board-facility" key={facility.id}>
                <div className="inline" style={{ justifyContent: 'space-between' }}><span>{facility.label}</span><b>{facility.value}</b></div>
                <Progress value={facility.value} tone={facility.value >= 75 ? 'ok' : facility.value >= 55 ? 'gold' : 'danger'} />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-2">
        <div className="inline" style={{ justifyContent: 'space-between' }}>
          <div><div className="cat">{t('PETICIONES A LA JUNTA')}</div><h3 style={{ margin: '3px 0 0' }}>{t('Inversión y proyecto')}</h3></div>
          <Badge tone="gold">{t('{count} disponibles', { count: data.requests.filter((request) => request.available).length })}</Badge>
        </div>
        <p className="small muted mt-1">{t('Cada petición consume caja y puede ser aprobada o rechazada según la confianza y el estado financiero. El historial queda registrado.')}</p>
        <div className="board-request-grid mt-2">
          {data.requests.map((request) => (
            <div className="board-request" key={request.id}>
              <div className="inline" style={{ justifyContent: 'space-between' }}>
                <Badge tone={request.available ? 'blue' : 'danger'}>{request.available ? t('Disponible') : t('Sin caja')}</Badge>
                <span className="small muted">{t('{value}% aprobación', { value: Math.round(request.approval_chance * 100) })}</span>
              </div>
              <h3>{t(request.label)}</h3>
              <p className="small muted">{t(request.description)}</p>
              <div className="board-request-numbers">
                <div><span>{t('Coste')}</span><b>{request.cost ? money(request.cost) : '—'}</b></div>
                <div><span>{t('Efecto')}</span><b>{t(request.effect_text)}</b></div>
              </div>
              <Button
                size="sm"
                variant="primary"
                icon={ArrowUpRight}
                onClick={() => makeRequest(request)}
                loading={busy === request.id}
                disabled={!request.available}
                data-testid={`board-request-${request.id}`}
              >
                {t('Solicitar')}
              </Button>
            </div>
          ))}
        </div>
      </Card>

      <div className="split-2 mt-2">
        <Card>
          <h3>{t('Junta directiva')}</h3>
          <div className="stack-sm mt-2">
            {data.board_members.map((member) => (
              <div className="board-member-row" key={`${member.role}-${member.name}`}>
                <span className="sponsor-mark"><Landmark size={16} /></span>
                <div><b>{member.name}</b><span>{t(member.role.replaceAll('_', ' '))}</span></div>
                <Badge tone={member.confidence === 'alta' ? 'ok' : member.confidence === 'media' ? 'gold' : 'neutral'}>{t(member.confidence)}</Badge>
              </div>
            ))}
            {!data.board_members.length && <p className="small muted">{t('La junta no tiene miembros registrados en esta partida.')}</p>}
          </div>
        </Card>

        <Card>
          <h3>{t('Historial de peticiones')}</h3>
          <div className="stack-sm mt-2">
            {data.history.map((entry, index) => (
              <div className="board-history-row" key={`${entry.date}-${entry.request_id}-${index}`}>
                <Badge tone={entry.approved ? 'ok' : 'danger'}>{entry.approved ? t('Aprobada') : t('Rechazada')}</Badge>
                <div><b>{t(entry.label)}</b><span>{dateLabel(entry.date)} · {entry.message}</span></div>
                <b className="small">{entry.cost ? money(entry.cost) : '—'}</b>
              </div>
            ))}
            {!data.history.length && <p className="small muted">{t('Todavía no has presentado ninguna petición a la junta.')}</p>}
          </div>
        </Card>
      </div>
    </>
  )
}
