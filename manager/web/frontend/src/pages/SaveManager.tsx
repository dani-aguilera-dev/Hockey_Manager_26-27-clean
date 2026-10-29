import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Check, FolderOpen, Pencil, Plus, Save, Search, Trash2, X } from 'lucide-react'
import { api } from '../lib/api'
import type { SaveEntry } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Crest, EmptyState, LoadingBlock, Logo, Modal } from '../components/ui'

export default function SaveManager() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [saves, setSaves] = useState<SaveEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [deleting, setDeleting] = useState<SaveEntry | null>(null)
  const [visible, setVisible] = useState(20)

  async function refresh() {
    try {
      const { data } = await api.get<{ saves: SaveEntry[] }>('/load')
      setSaves(data.saves)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudieron cargar las partidas.', 'danger')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return saves
    return saves.filter((save) => [save.name, save.club_name, save.season].some((value) => value.toLowerCase().includes(needle)))
  }, [saves, query])

  async function load(save: SaveEntry) {
    setBusy(`load-${save.name}`)
    try {
      await api.post('/load', { name: save.name })
      navigate('/game')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo cargar la partida.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  function startRename(save: SaveEntry) {
    setEditing(save.name)
    setDraft(save.name)
  }

  async function rename(save: SaveEntry) {
    const newName = draft.trim()
    if (!newName) {
      toast('El nombre no puede estar vacío.', 'danger')
      return
    }
    if (newName === save.name) {
      setEditing(null)
      return
    }
    setBusy(`rename-${save.name}`)
    try {
      const { data } = await api.patch<{ saves: SaveEntry[] }>('/saves', { name: save.name, new_name: newName })
      setSaves(data.saves)
      setEditing(null)
      toast('Partida renombrada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo renombrar la partida.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function remove() {
    if (!deleting) return
    const save = deleting
    setBusy(`delete-${save.name}`)
    try {
      const { data } = await api.delete<{ saves: SaveEntry[] }>('/saves', { name: save.name })
      setSaves(data.saves)
      setDeleting(null)
      toast('Partida eliminada.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo eliminar la partida.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="landing">
      <div className="landing-inner" style={{ maxWidth: 980 }}>
        <header className="landing-header">
          <Logo />
          <nav className="landing-nav">
            <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate('/')}>Volver</Button>
            <Button variant="primary" icon={Plus} onClick={() => navigate('/new')}>Nueva partida</Button>
          </nav>
        </header>

        <div className="eyebrow">Gestión de partidas</div>
        <h1 style={{ fontSize: 40 }}>Tus carreras, bajo control.</h1>
        <p className="landing-sub" style={{ marginBottom: 20 }}>
          Carga, renombra o elimina partidas guardadas. Los cambios se aplican en la base de datos local de la web.
        </p>

        <div className="inline" style={{ justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 14 }}>
          <label className="search-box" style={{ marginBottom: 0 }}>
            <Search size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar partida, club o temporada…" aria-label="Buscar partida" />
          </label>
          <Badge tone="neutral">{saves.length} guardadas</Badge>
        </div>

        {loading ? <LoadingBlock label="Leyendo partidas guardadas…" /> : filtered.length ? (
          <div className="save-list">
            {filtered.slice(0, visible).map((save) => {
              const isEditing = editing === save.name
              const isBusy = busy?.endsWith(save.name)
              return (
                <div className="save-row" key={save.id}>
                  <Crest src={save.crest} name={save.club_name} size={40} />
                  <div className="save-row-main">
                    {isEditing ? (
                      <input
                        autoFocus
                        value={draft}
                        onChange={(event) => setDraft(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') void rename(save)
                          if (event.key === 'Escape') setEditing(null)
                        }}
                        aria-label="Nombre de la partida"
                        maxLength={90}
                      />
                    ) : (
                      <b>{save.name}</b>
                    )}
                    <span>{save.club_name} · {save.season} · Jornada {save.round} · {save.updated_at.replace('T', ' ').slice(0, 16)}</span>
                  </div>
                  {save.is_current && <Badge tone="gold">Actual</Badge>}
                  <div className="save-row-actions">
                    {isEditing ? (
                      <>
                        <Button size="sm" variant="primary" icon={Check} onClick={() => rename(save)} loading={isBusy}>Guardar</Button>
                        <Button size="sm" variant="ghost" icon={X} onClick={() => setEditing(null)}>Cancelar</Button>
                      </>
                    ) : (
                      <>
                        <Button size="sm" icon={Pencil} onClick={() => startRename(save)} disabled={!!busy}>Renombrar</Button>
                        <Button size="sm" variant="danger" icon={Trash2} onClick={() => setDeleting(save)} disabled={!!busy}>Eliminar</Button>
                        <Button size="sm" variant="primary" icon={ArrowRight} onClick={() => load(save)} loading={busy === `load-${save.name}`}>Cargar</Button>
                      </>
                    )}
                  </div>
                </div>
              )
            })}
            {filtered.length > visible && (
              <div className="actions mt-2" style={{ justifyContent: 'center' }}>
                <Button variant="ghost" onClick={() => setVisible((current) => current + 20)}>Mostrar más ({filtered.length - visible})</Button>
              </div>
            )}
          </div>
        ) : (
          <EmptyState
            title={saves.length ? 'No hay partidas que coincidan' : 'No hay partidas guardadas'}
            body={saves.length ? 'Prueba con otro nombre, club o temporada.' : 'Crea una nueva carrera para empezar.'}
            action={<Button variant="primary" icon={Save} onClick={() => navigate('/new')}>Nueva partida</Button>}
          />
        )}

        <div className="landing-footer" style={{ marginTop: 28 }}>
          <FolderOpen size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />
          Las partidas se guardan automáticamente al avanzar y manualmente con el botón de guardar.
        </div>
      </div>

      <Modal open={!!deleting} title="Eliminar partida" onClose={() => setDeleting(null)}>
        <p>
          ¿Seguro que quieres eliminar <b>{deleting?.name}</b>? Esta acción no se puede deshacer.
        </p>
        {deleting?.is_current && (
          <p className="small muted">
            Es la partida que tienes abierta. El juego seguirá en memoria, pero dejará de estar guardado en disco hasta que vuelvas a guardar.
          </p>
        )}
        <div className="actions mt-2" style={{ justifyContent: 'flex-end' }}>
          <Button variant="ghost" onClick={() => setDeleting(null)}>Cancelar</Button>
          <Button variant="danger" icon={Trash2} onClick={remove} loading={!!deleting && busy === `delete-${deleting.name}`}>Eliminar</Button>
        </div>
      </Modal>
    </div>
  )
}
