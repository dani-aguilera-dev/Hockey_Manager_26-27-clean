import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, FolderOpen, Save, Search } from 'lucide-react'
import { api } from '../lib/api'
import type { SaveEntry } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Crest, EmptyState, LoadingBlock, Logo } from '../components/ui'

export default function LoadGame() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [saves, setSaves] = useState<SaveEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [visible, setVisible] = useState(12)

  useEffect(() => {
    api.get<{ saves: SaveEntry[] }>('/load')
      .then(({ data }) => setSaves(data.saves))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudieron cargar las partidas.', 'danger'))
      .finally(() => setLoading(false))
  }, [toast])

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return saves
    return saves.filter((save) => [save.name, save.club_name, save.season].some((value) => value.toLowerCase().includes(needle)))
  }, [saves, query])

  async function load(save: SaveEntry) {
    setBusy(save.name)
    try {
      await api.post('/load', { name: save.name })
      navigate('/game')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo cargar la partida.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="landing">
      <div className="landing-inner" style={{ maxWidth: 900 }}>
        <header className="landing-header">
          <Logo />
          <div className="inline" style={{ gap: 6 }}>
            <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate('/')}>Volver</Button>
            <Button variant="ghost" icon={FolderOpen} onClick={() => navigate('/saves')}>Gestionar</Button>
          </div>
        </header>
        <div className="eyebrow">Cargar partida</div>
        <h1 style={{ fontSize: 40 }}>Tu carrera, donde la dejaste.</h1>
        <p className="landing-sub" style={{ marginBottom: 24 }}>Las partidas se guardan en la base de datos local de la web.</p>
        <label className="search-box" style={{ marginBottom: 14 }}>
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar partida, club o temporada…" aria-label="Buscar partida" />
        </label>

        {loading ? <LoadingBlock /> : filtered.length ? (
          <div className="save-list">
            {filtered.slice(0, visible).map((save) => (
              <div className="save-row" key={save.id}>
                <Crest src={save.crest} name={save.club_name} size={40} />
                <div className="save-row-main">
                  <b>{save.name}</b>
                  <span>{save.club_name} · {save.season} · Jornada {save.round} · {save.updated_at.replace('T', ' ').slice(0, 16)}</span>
                </div>
                {save.is_current && <Badge tone="gold">Actual</Badge>}
                <Button variant="primary" icon={ArrowRight} onClick={() => load(save)} loading={busy === save.name}>Cargar</Button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No hay partidas guardadas" body="Crea una nueva carrera para empezar." action={<Button variant="primary" icon={Save} onClick={() => navigate('/new')}>Nueva partida</Button>} />
        )}
        {filtered.length > visible && <div className="actions mt-2" style={{ justifyContent: 'center' }}><Button variant="ghost" onClick={() => setVisible((current) => current + 12)}>Mostrar más ({filtered.length - visible})</Button></div>}
      </div>
    </div>
  )
}
