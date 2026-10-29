import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, ChevronRight, MessageSquare, Plus, Search, Sparkles, UserRound, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel } from '../lib/format'
import type { ChatMessage, ChatPayload, ChatTarget, ChatTopic, ChatTopicsPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, EmptyState, LoadingBlock, Modal, PageHeader } from '../components/ui'

type Filter = 'all' | 'pending' | 'player' | 'staff' | 'answered'

function targetAvatar(target: ChatTarget) {
  return { name: target.name, photo: target.photo, initials: target.initials }
}

function ageBandLabel(value?: string) {
  if (value === 'joven') return 'Joven'
  if (value === 'madurez') return 'Madurez'
  if (value === 'veterano') return 'Veterano'
  return value
}

export default function ChatPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { refresh } = useGame()
  const { toast } = useToast()
  const deepOpened = useRef(false)
  const [data, setData] = useState<ChatPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [pickerOpen, setPickerOpen] = useState(false)
  const [pickerTab, setPickerTab] = useState<'players' | 'staff'>('players')
  const [search, setSearch] = useState('')
  const [selectedTarget, setSelectedTarget] = useState<ChatTarget | null>(null)
  const [topics, setTopics] = useState<ChatTopic[]>([])
  const [topicsLoading, setTopicsLoading] = useState(false)

  function load() {
    setLoading(true)
    api.get<ChatPayload>('/chat')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el vestuario.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    if (!data || deepOpened.current) return
    const targetType = searchParams.get('target_type')
    const targetId = searchParams.get('target_id')
    if (!targetType || !targetId) return
    const list = targetType === 'staff' ? data.targets.staff : data.targets.players
    const target = list.find((item) => item.target_id === targetId)
    if (!target) return
    deepOpened.current = true
    setPickerOpen(true)
    void chooseTarget(target)
  }, [data, searchParams])

  const pending = data?.messages.filter((message) => !message.answered).length || 0
  const players = data?.targets.players || []
  const staff = data?.targets.staff || []
  const targets = pickerTab === 'players' ? players : staff
  const filteredTargets = useMemo(() => {
    const needle = search.trim().toLowerCase()
    if (!needle) return targets
    return targets.filter((target) =>
      [target.name, target.role, target.position, target.performance].filter(Boolean).some((value) => String(value).toLowerCase().includes(needle)),
    )
  }, [targets, search])

  const messages = useMemo(() => {
    if (!data) return []
    return data.messages.filter((message) => {
      if (filter === 'pending') return !message.answered
      if (filter === 'answered') return message.answered
      if (filter === 'player') return message.target_type !== 'staff'
      if (filter === 'staff') return message.target_type === 'staff'
      return true
    })
  }, [data, filter])

  function openPicker() {
    setPickerOpen(true)
    setSelectedTarget(null)
    setTopics([])
    setSearch('')
  }

  async function chooseTarget(target: ChatTarget) {
    setSelectedTarget(target)
    setTopicsLoading(true)
    try {
      const { data } = await api.get<ChatTopicsPayload>(`/chat/topics?target_type=${target.target_type}&target_id=${encodeURIComponent(target.target_id)}`)
      setTopics(data.topics)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudieron cargar los temas.', 'danger')
    } finally {
      setTopicsLoading(false)
    }
  }

  async function startTopic(topic: ChatTopic) {
    if (!selectedTarget) return
    setBusy(`start-${topic.id}`)
    try {
      const response = await api.post<ChatPayload>(`/chat/start`, {
        target_type: selectedTarget.target_type,
        target_id: selectedTarget.target_id,
        topic: topic.id,
      })
      setData(response.data)
      setPickerOpen(false)
      setFilter('all')
      await refresh()
      toast(response.message || 'Conversación abierta.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo abrir la conversación.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function answer(message: ChatMessage, optionIndex: number) {
    setBusy(message.id)
    try {
      const response = await api.post<ChatPayload>(`/chat/${message.id}`, { option: optionIndex })
      setData(response.data)
      await refresh()
      toast(response.message || 'Conversación registrada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo responder.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function randomChat() {
    setBusy('random')
    try {
      const response = await api.post<ChatPayload>('/chat/new')
      setData(response.data)
      setFilter('all')
      await refresh()
      toast(response.message || 'Conversación abierta.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo abrir una conversación.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Entrando al vestuario…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el vestuario.</p></Card>

  const averageRelationship = Math.round(
    [...players, ...staff].reduce((sum, target) => sum + target.relationship, 0) / Math.max(1, players.length + staff.length),
  )

  return (
    <>
      <PageHeader
        eyebrow="Vestuario · relaciones y liderazgo"
        title="Conversaciones"
        subtitle="Habla con cualquier jugador o empleado. El tema y las respuestas cambian según edad, rol, rendimiento, contrato y mercado."
        actions={<><Button icon={ArrowLeft} onClick={() => navigate('/game')}>Volver al club</Button><Button variant="primary" icon={Plus} onClick={openPicker}>Nueva conversación</Button><Button icon={Sparkles} onClick={randomChat} loading={busy === 'random'}>Aleatoria</Button></>}
      />

      <div className="dashboard-kpis">
        <div className="stat-card"><span className="stat-top">PENDIENTES</span><strong>{pending}</strong><small>Conversaciones sin responder</small></div>
        <div className="stat-card"><span className="stat-top">JUGADORES</span><strong>{players.length}</strong><small>Objetivos disponibles</small></div>
        <div className="stat-card"><span className="stat-top">STAFF</span><strong>{staff.length}</strong><small>Empleados disponibles</small></div>
        <div className="stat-card"><span className="stat-top">RELACIÓN MEDIA</span><strong>{averageRelationship}/100</strong><small>Con el grupo y el staff</small></div>
      </div>

      <Card>
        <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
          <div className="tabs">
            {([
              ['all', 'Todas'],
              ['pending', 'Pendientes'],
              ['player', 'Jugadores'],
              ['staff', 'Staff'],
              ['answered', 'Historial'],
            ] as Array<[Filter, string]>).map(([value, label]) => (
              <button key={value} type="button" className={`tab ${filter === value ? 'active' : ''}`} onClick={() => setFilter(value)}>{label}</button>
            ))}
          </div>
          <Badge tone="neutral">{messages.length} conversaciones</Badge>
        </div>

        {messages.length ? (
          <div className="chat-list">
            {messages.map((message) => {
              const player = data.players[message.player_id]
              const staffMember = message.staff_role ? data.staff[message.staff_role] : null
              const isStaff = message.target_type === 'staff'
              const target = isStaff ? staffMember : player
              const name = message.target_name || message.player_name || target?.name || 'Vestuario'
              const initials = message.target_initials || name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
              return (
                <Card key={message.id} className={`chat-card ${message.answered ? '' : 'pending'}`}>
                  <div className="chat-head">
                    <div className="chat-head-main">
                      <Avatar player={{ name, photo: message.target_photo_url || message.target_photo || (target as { photo?: string } | undefined)?.photo, initials }} size={44} />
                      <div>
                        <div className="inline">
                          <b>{name}</b>
                          {isStaff ? <Badge tone="blue">Staff</Badge> : <Badge tone="neutral">{message.context?.age ? `${message.context.age} años` : message.target_role}</Badge>}
                          {message.topic_label && <Badge tone="gold">{message.topic_label}</Badge>}
                        </div>
                        <span className="chat-meta">{message.context?.performance || message.target_role || 'Conversación'} · relación {message.relationship}/100 · {dateLabel(message.date)}</span>
                      </div>
                    </div>
                    <Badge tone={message.answered ? 'ok' : 'warn'}>{message.answered ? 'Respondida' : 'Pendiente'}</Badge>
                  </div>

                  {message.context && (
                    <div className="chat-context">
                      {message.context.role && <span>{message.context.role}</span>}
                      {message.context.age_band && <span>{ageBandLabel(message.context.age_band)}</span>}
                      {message.context.performance && <span>{message.context.performance}</span>}
                      {message.context.contract_status && message.context.contract_status !== 'largo' && <span>Contrato: {message.context.contract_status}</span>}
                      {message.context.market_interest && <span className="gold">Interés de mercado</span>}
                    </div>
                  )}

                  {message.turns?.length ? (
                    <div className="chat-transcript">
                      {message.turns.map((turn, index) => (
                        <div className={`chat-turn ${turn.speaker}`} key={`${message.id}-turn-${index}`}>
                          <span className="chat-turn-role">{turn.speaker === 'manager' ? 'Tú' : name}</span>
                          <p>{turn.text}</p>
                          {turn.headline && <Badge tone={turn.tone === 'danger' ? 'danger' : turn.tone === 'ok' ? 'ok' : 'neutral'}>{turn.headline}</Badge>}
                        </div>
                      ))}
                    </div>
                  ) : <p>{message.text}</p>}
                  {!message.answered ? (
                    <div className="option-list">
                      {message.options.map((option, index) => (
                        <button type="button" className="option-card chat-option" key={`${option.label}-${index}`} onClick={() => answer(message, index)} disabled={busy === message.id}>
                          <span className={`chat-option-tone tone-${option.tone || 'neutral'}`} />
                          <span><b>{option.label}</b>{option.headline && <><br /><span>{option.headline}</span></>}</span>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="chat-answer">
                      {message.answer && <p className="small muted"><b>Última decisión:</b> {message.answer}</p>}
                      {message.headline && <Badge tone={message.tone === 'danger' ? 'danger' : message.tone === 'ok' ? 'ok' : 'neutral'}>{message.headline}</Badge>}
                      {!message.turns?.length && message.response && <p className="small">{message.response}</p>}
                    </div>
                  )}
                </Card>
              )
            })}
          </div>
        ) : <EmptyState title="Sin conversaciones en este filtro" body="Abre una nueva conversación con cualquier jugador o empleado del club." action={<Button variant="primary" icon={Plus} onClick={openPicker}>Nueva conversación</Button>} />}
      </Card>

      <Modal open={pickerOpen} title="Nueva conversación" onClose={() => setPickerOpen(false)} wide>
        {!selectedTarget ? (
          <>
            <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
              <div className="tabs">
                <button type="button" className={`tab ${pickerTab === 'players' ? 'active' : ''}`} onClick={() => { setPickerTab('players'); setSearch('') }}><Users size={13} /> Jugadores ({players.length})</button>
                <button type="button" className={`tab ${pickerTab === 'staff' ? 'active' : ''}`} onClick={() => { setPickerTab('staff'); setSearch('') }}><UserRound size={13} /> Staff ({staff.length})</button>
              </div>
              <label className="search-box" style={{ maxWidth: 240 }}>
                <Search size={15} />
                <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por nombre o rol…" />
              </label>
            </div>
            <div className="chat-target-list">
              {filteredTargets.map((target) => (
                <button type="button" className="chat-target-row" key={`${target.target_type}-${target.target_id}`} onClick={() => chooseTarget(target)}>
                  <Avatar player={targetAvatar(target)} size={40} />
                  <span className="chat-target-main">
                    <b>{target.name}</b>
                    <span>{target.target_type === 'staff' ? `${target.role} · ${target.rating}/100` : `${target.age} años · ${target.position} · OVR ${target.overall?.toFixed(1)}`}</span>
                    <span className="small muted">{target.performance || target.role} · relación {target.relationship}/100 · {target.topic_count} temas</span>
                  </span>
                  <ChevronRight size={16} className="muted" />
                </button>
              ))}
              {!filteredTargets.length && <p className="small muted">No hay objetivos que coincidan.</p>}
            </div>
          </>
        ) : (
          <>
            <div className="inline" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
              <div className="inline"><Avatar player={targetAvatar(selectedTarget)} size={36} /><div><b>{selectedTarget.name}</b><div className="small muted">{selectedTarget.target_type === 'staff' ? selectedTarget.role : `${selectedTarget.age} años · ${selectedTarget.position}`}</div></div></div>
              <Button size="sm" variant="ghost" onClick={() => { setSelectedTarget(null); setTopics([]) }}>Cambiar objetivo</Button>
            </div>
            {topicsLoading ? <LoadingBlock label="Preparando temas de conversación…" /> : (
              <div className="topic-grid">
                {topics.map((topic) => (
                  <button type="button" className="topic-card" key={topic.id} onClick={() => startTopic(topic)} disabled={Boolean(busy)}>
                    <span className="cat">{topic.category}</span>
                    <b>{topic.label}</b>
                    <span>{topic.description}</span>
                    <span className="topic-badges">
                      {topic.recommended && <Badge tone="gold">Sugerido</Badge>}
                      {topic.recent && <Badge tone="neutral">Reciente</Badge>}
                    </span>
                    <ChevronRight size={15} />
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </Modal>
    </>
  )
}
