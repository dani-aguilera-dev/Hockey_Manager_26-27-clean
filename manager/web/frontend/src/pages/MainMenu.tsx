import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, CalendarDays, ChevronRight, CircleDot, FolderOpen, LogOut, Plus, Save, Settings, Shield, Trophy, Users } from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, shortLeague } from '../lib/format'
import type { MenuData, SaveEntry } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, Crest, LoadingBlock, Logo } from '../components/ui'

export default function MainMenu() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [data, setData] = useState<MenuData | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      const response = await api.get<MenuData>('/menu')
      setData(response.data)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo cargar el menú.', 'danger')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function loadSave(save: SaveEntry) {
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

  async function exitGame() {
    setBusy('exit')
    try {
      await api.post('/exit')
      await load()
      toast('Partida guardada. Has vuelto al inicio.', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo salir.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  const current = data?.current
  const saves = data?.saves || []

  return (
    <div className="landing">
      <div className="landing-inner">
        <header className="landing-header">
          <Logo />
          <nav className="landing-nav">
            <Button variant="ghost" icon={Settings} onClick={() => navigate('/options')}>Ajustes</Button>
            <Button variant="ghost" icon={FolderOpen} onClick={() => navigate('/saves')}>Gestionar partidas</Button>
            <Button variant="primary" icon={Plus} onClick={() => navigate('/new')}>Nueva partida</Button>
          </nav>
        </header>

        {loading ? (
          <div className="app-loading" style={{ minHeight: '55vh' }}><LoadingBlock label="Cargando menú…" /></div>
        ) : (
          <>
            <section className="landing-hero">
              <div>
                <div className="landing-kicker">Hockey Manager · Web</div>
                <h1 className="landing-title">Dirige el club.<br /><span>Lee el juego.</span></h1>
                <p className="landing-sub">
                  Ocho competiciones, plantillas reales, partido en directo, mercado, vestuario y una temporada que se construye día a día.
                  La oficina del entrenador, ahora en el navegador.
                </p>
                <div className="landing-actions">
                  {current ? (
                    <Button variant="primary" size="lg" icon={ArrowRight} onClick={() => navigate(current.live_active ? '/game/live' : '/game')}>
                      {current.live_active ? 'Continuar partido' : 'Continuar partida'}
                    </Button>
                  ) : (
                    <Button variant="primary" size="lg" icon={Plus} onClick={() => navigate('/new')}>Empezar una carrera</Button>
                  )}
                  <Button size="lg" icon={Save} onClick={() => navigate('/load')}>Cargar partida</Button>
                </div>
              </div>
              <aside className="landing-side">
                <div className="landing-side-label">El producto</div>
                <div className="landing-facts">
                  <div className="landing-fact"><b>8</b><span>competiciones jugables</span></div>
                  <div className="landing-fact"><b>+1.000</b><span>jugadores con datos</span></div>
                  <div className="landing-fact"><b>6</b><span>ligas internacionales</span></div>
                  <div className="landing-fact"><b>100%</b><span>interfaz React</span></div>
                </div>
              </aside>
            </section>

            {current && (
              <section className="landing-section">
                <div className="landing-section-head">
                  <h2>Partida en curso</h2>
                  <Badge tone={current.live_active ? 'danger' : 'ok'}>{current.live_active ? 'Partido en directo' : 'En juego'}</Badge>
                </div>
                <Card className="current-card">
                  <div className="current-team">
                    <Crest src={current.team.crest} name={current.team.name} size={68} />
                    <div>
                      <div className="eyebrow">{shortLeague(current.competition.code)} · {current.competition.country}</div>
                      <h2>{current.team.name}</h2>
                      <p>{current.season} · Jornada {current.round} · {dateLabel(current.date)} · {current.save_name}</p>
                    </div>
                  </div>
                  <div className="actions">
                    <Button variant="primary" icon={ArrowRight} onClick={() => navigate(current.live_active ? '/game/live' : '/game')}>Continuar</Button>
                    <Button icon={Save} onClick={() => navigate('/load')}>Cargar otra</Button>
                    <Button variant="ghost" icon={FolderOpen} onClick={() => navigate('/saves')}>Gestionar guardadas</Button>
                    <Button variant="ghost" icon={LogOut} onClick={exitGame} loading={busy === 'exit'}>Cerrar partida</Button>
                  </div>
                </Card>
              </section>
            )}

            <div className="landing-body">
              <section>
                <div className="landing-section-head">
                  <h2>Partidas guardadas</h2>
                  <div className="inline" style={{ gap: 6 }}>
                    <Button variant="ghost" size="sm" icon={FolderOpen} onClick={() => navigate('/saves')}>Gestionar</Button>
                    <Button variant="ghost" size="sm" onClick={() => navigate('/load')}>Ver todas ({saves.length})</Button>
                  </div>
                </div>
                {saves.length ? (
                  <div className="save-list">
                    {saves.slice(0, 5).map((save) => (
                      <div className="save-row" key={save.id}>
                        <Crest src={save.crest} name={save.club_name} size={34} />
                        <div className="save-row-main">
                          <b>{save.name}</b>
                          <span>{save.club_name} · {save.season} · J{save.round} · {save.updated_at.replace('T', ' ').slice(0, 16)}</span>
                        </div>
                        {save.is_current && <Badge tone="gold">Actual</Badge>}
                        <Button size="sm" onClick={() => loadSave(save)} loading={busy === save.name}>Cargar</Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Card><p className="muted small" style={{ margin: 0 }}>Todavía no hay partidas guardadas. Empieza una carrera y el juego guardará automáticamente.</p></Card>
                )}
              </section>

              <section>
                <div className="landing-section-head"><h2>Una carrera, muchas decisiones</h2></div>
                <div className="landing-features">
                  <div className="landing-feature"><Trophy size={20} /><h3>Competición</h3><p>DHA, DHB, Hoofdklasse, Bélgica, Bundesliga, Inglaterra, Argentina e India.</p></div>
                  <div className="landing-feature"><Users size={20} /><h3>Vestuario</h3><p>Moral, relaciones, charlas, prensa y un grupo que reacciona a tus decisiones.</p></div>
                  <div className="landing-feature"><CalendarDays size={20} /><h3>Día a día</h3><p>Simula el calendario, prepara la semana y llega al partido con el trabajo hecho.</p></div>
                </div>
              </section>
            </div>

            <div className="landing-footer">
              Hockey Manager · proyecto personal/educativo · fotos y escudos de clubes, ligas y autores · interfaz React + Flask
            </div>
          </>
        )}
      </div>
    </div>
  )
}
