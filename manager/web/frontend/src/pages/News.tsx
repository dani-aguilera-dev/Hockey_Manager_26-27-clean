import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Award, ChevronRight, Newspaper, Tag } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { Award as AwardType, DailyEvent, NewsItem } from '../types'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, Crest, EmptyState, LoadingBlock, Modal, PageHeader } from '../components/ui'

interface NewsPayload {
  news: NewsItem[]
  awards: AwardType[]
  daily_events: DailyEvent[]
}

const filters = ['Todo', 'Partido', 'Rendimiento', 'Liga', 'Mercado', 'Rumor', 'Cantera', 'Club', 'Ascenso', 'Premios']

export default function NewsPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [data, setData] = useState<NewsPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('Todo')
  const [selected, setSelected] = useState<NewsItem | null>(null)

  useEffect(() => {
    api.get<NewsPayload>('/news')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar las noticias.', 'danger'))
      .finally(() => setLoading(false))
  }, [toast])

  const filtered = useMemo(() => {
    if (!data) return []
    if (filter === 'Todo') return data.news
    if (filter === 'Premios') return data.news.filter((item) => (item.awards?.length || 0) > 0)
    return data.news.filter((item) => item.category === filter)
  }, [data, filter])

  if (loading) return <LoadingBlock label="Cargando actualidad…" />
  if (!data) return <Card><p className="muted">No se pudieron cargar las noticias.</p></Card>

  const lead = filtered[0]

  return (
    <>
      <PageHeader
        eyebrow="Actualidad · datos reales de la partida"
        title="Noticias"
        subtitle="Resultados, rendimiento, rumores de mercado, premios individuales y todo lo que pasa en el club."
        actions={<Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button>}
      />

      {data.awards.length > 0 && (
        <section className="award-strip">
          <div className="award-strip-head"><div><div className="cat">PREMIOS DE LA JORNADA</div><h2>Los nombres del último partido</h2></div><Award size={22} className="gold" /></div>
          <div className="award-grid">
            {data.awards.map((award) => (
              <button type="button" className="award-card" key={award.id} onClick={() => navigate(`/game/player/${award.player_id}`)}>
                <Avatar player={{ name: award.player_name, photo: award.photo }} size={30} />
                <span className="award-main"><b>{award.player_name}</b><span>{award.label} · {award.value}</span></span>
                {award.team_crest && <Crest src={award.team_crest} name={award.team_name} size={24} />}
              </button>
            ))}
          </div>
        </section>
      )}

      <div className="news-filters">
        {filters.map((item) => (
          <button type="button" key={item} className={`news-filter ${filter === item ? 'active' : ''}`} onClick={() => setFilter(item)}>
            {item}{item === 'Premios' ? ` (${data.awards.length})` : ''}
          </button>
        ))}
      </div>

      {lead ? (
        <Card className="feature-news news-feature" padded={false}>
          <div className="feature-media news-feature-media">
            {lead.crest ? <Crest src={lead.crest} name={lead.headline} size={82} /> : lead.photo_url ? <Avatar player={{ name: lead.headline, photo: lead.photo_url }} size={82} /> : <Newspaper size={36} />}
            {lead.crest2 && <Crest src={lead.crest2} name={lead.headline} size={82} />}
          </div>
          <div className="feature-body">
            <div className="inline"><span className="cat">{lead.category} · {dateLabel(lead.date)}</span>{lead.hot && <Badge tone="danger">Última hora</Badge>}</div>
            <h1>{lead.headline}</h1>
            <p>{lead.body}</p>
            <div className="news-tags">{lead.tags?.map((tag) => <Badge tone="neutral" key={tag}>{tag}</Badge>)}</div>
            <div className="actions mt-2">
              <Button variant="primary" onClick={() => setSelected(lead)}>Ver noticia completa</Button>
              {lead.related_teams?.slice(0, 2).map((team) => <Button size="sm" key={team.id} onClick={() => navigate(`/game/team/${team.id}`)}>{team.name}</Button>)}
            </div>
          </div>
        </Card>
      ) : <EmptyState title="Sin noticias en este filtro" body="Prueba con otra categoría o avanza el calendario." />}

      <div className="news-grid">
        {filtered.slice(1).map((item) => (
          <button type="button" className="news-card news-card-click" key={item.id || `${item.headline}-${item.date}`} onClick={() => setSelected(item)}>
            <div className="news-card-media">
              {item.crest ? <Crest src={item.crest} name={item.headline} size={42} /> : item.photo_url ? <Avatar player={{ name: item.headline, photo: item.photo_url }} size={42} /> : <Newspaper size={20} />}
              {item.crest2 && <Crest src={item.crest2} name={item.headline} size={42} />}
            </div>
            <div className="news-copy">
              <div className="inline"><span className="cat">{item.category} · {dateLabel(item.date)}</span>{item.hot && <Badge tone="danger">Hot</Badge>}</div>
              <h3>{item.headline}</h3>
              <p>{item.summary || item.body}</p>
              <div className="news-tags">{item.tags?.slice(0, 3).map((tag) => <Badge tone="neutral" key={tag}>{tag}</Badge>)}</div>
              <span className="news-read">Leer noticia <ChevronRight size={13} /></span>
            </div>
          </button>
        ))}
      </div>

      {data.daily_events.length > 0 && (
        <Card className="mt-2">
          <div className="inline" style={{ justifyContent: 'space-between' }}><h2 style={{ margin: 0 }}>Diario del club</h2><Badge tone="neutral">{data.daily_events.length} eventos</Badge></div>
          <div className="news-list mt-2">
            {data.daily_events.map((event, index) => (
              <div className="news-item" key={`${event.headline}-${index}`}>
                <div className="news-copy"><div className="cat">{event.category} · {dateLabel(event.date)}{event.league ? ` · ${event.league}` : ''}</div><h3>{event.headline}</h3><p>{event.body}</p></div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Modal open={Boolean(selected)} title={selected?.headline || 'Noticia'} onClose={() => setSelected(null)} wide>
        {selected && (
          <article className="news-detail">
            <div className="inline"><Badge tone="gold">{selected.category}</Badge><span className="small muted">{dateLabel(selected.date)}</span>{selected.hot && <Badge tone="danger">Última hora</Badge>}</div>
            <div className="news-detail-hero">
              {selected.crest && <Crest src={selected.crest} name={selected.headline} size={70} />}
              {selected.crest2 && <Crest src={selected.crest2} name={selected.headline} size={70} />}
              <div><h2>{selected.headline}</h2><p>{selected.body}</p></div>
            </div>
            {selected.stats && Object.keys(selected.stats).length > 0 && (
              <div className="news-detail-stats">
                {Object.entries(selected.stats).map(([label, value]) => <div key={label}><span>{label}</span><b>{String(value)}</b></div>)}
              </div>
            )}
            {selected.awards?.length ? (
              <section>
                <h3>Premios individuales</h3>
                <div className="award-grid">
                  {selected.awards.map((award) => (
                    <button type="button" className="award-card" key={award.id} onClick={() => navigate(`/game/player/${award.player_id}`)}>
                      <Avatar player={{ name: award.player_name, photo: award.photo }} size={30} />
                      <span className="award-main"><b>{award.player_name}</b><span>{award.label} · {award.value}</span></span>
                    </button>
                  ))}
                </div>
              </section>
            ) : null}
            {selected.related_teams?.length ? (
              <section>
                <h3>Equipos relacionados</h3>
                <div className="news-related-grid">
                  {selected.related_teams.map((team) => (
                    <button type="button" className="news-related-row" key={team.id} onClick={() => navigate(`/game/team/${team.id}`)}>
                      <Crest src={team.crest} name={team.name} size={30} />
                      <span><b>{team.name}</b><span>{team.city} · {team.points} pts · {team.position || '—'}º</span></span>
                      <ArrowRight size={14} />
                    </button>
                  ))}
                </div>
              </section>
            ) : null}
            {selected.related_players?.length ? (
              <section>
                <h3>Jugadores relacionados</h3>
                <div className="news-related-grid">
                  {selected.related_players.map((player) => (
                    <button type="button" className="news-related-row" key={player.id} onClick={() => navigate(`/game/player/${player.id}`)}>
                      <Avatar player={player} size={30} />
                      <span><b>{player.name}</b><span>{player.subposition} · {player.age} años · OVR {player.overall.toFixed(1)}</span></span>
                      <ArrowRight size={14} />
                    </button>
                  ))}
                </div>
              </section>
            ) : null}
            <div className="news-tags">{selected.tags?.map((tag) => <Badge tone="neutral" key={tag}><Tag size={10} /> {tag}</Badge>)}</div>
          </article>
        )}
      </Modal>
    </>
  )
}
