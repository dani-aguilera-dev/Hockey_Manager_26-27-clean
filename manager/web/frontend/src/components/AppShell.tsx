import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowLeftRight,
  Building2,
  CalendarDays,
  ChevronRight,
  ClipboardList,
  Dumbbell,
  Flag,
  FolderOpen,
  HeartPulse,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Menu,
  MessageSquare,
  Newspaper,
  Save,
  Settings,
  Shield,
  Trophy,
  Users,
  X,
} from 'lucide-react'
import { api } from '../lib/api'
import { dateLabel, shortLeague } from '../lib/format'
import type { GameState } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Crest, LoadingBlock, Logo } from './ui'

const primary = [
  { to: '/game', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/game/decisions', label: 'Decisiones', icon: ListChecks },
  { to: '/game/news', label: 'Actualidad', icon: Newspaper },
  { to: '/game/chat', label: 'Vestuario', icon: MessageSquare },
]

const teamLinks = [
  { to: '/game/squad', label: 'Plantilla', icon: Users },
  { to: '/game/tactics', label: 'Táctica', icon: ClipboardList },
  { to: '/game/training', label: 'Entrenamiento', icon: Dumbbell },
  { to: '/game/medical', label: 'Enfermería', icon: HeartPulse },
]

const competitionLinks = [
  { to: '/game/calendar', label: 'Calendario y amistosos', icon: CalendarDays },
  { to: '/game/match', label: 'Próximo partido', icon: Flag },
  { to: '/game/table', label: 'Clasificación', icon: Trophy },
  { to: '/game/objectives', label: 'Objetivos', icon: Trophy },
  { to: '/game/cup', label: 'Copa del Rey', icon: Shield },
  { to: '/game/ehl', label: 'Europa · EHL', icon: CalendarDays },
]

const clubLinks = [
  { to: '/game/market', label: 'Mercado', icon: ArrowLeftRight },
  { to: '/game/commercial', label: 'Comercial y marca', icon: Building2 },
  { to: '/game/staff', label: 'Staff y junta', icon: Users },
  { to: '/game/youth', label: 'Cantera', icon: Shield },
  { to: '/game/press', label: 'Prensa', icon: Newspaper },
]

function NavGroup({ title, links, onNavigate }: { title: string; links: typeof primary; onNavigate?: () => void }) {
  return (
    <div className="nav-group">
      <div className="nav-group-title">{title}</div>
      {links.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <Icon size={17} />
          <span>{label}</span>
        </NavLink>
      ))}
    </div>
  )
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { game } = useGame()
  if (!game) return null
  const links = game.objectives?.system === 'regional'
    ? [...competitionLinks, { to: '/game/promotion', label: 'Fase de ascenso', icon: Trophy }]
    : competitionLinks
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <Logo />
      </div>
      <div className="sidebar-club">
        <Crest src={game.team.crest} name={game.team.name} size={38} />
        <div>
          <b>{game.team.name}</b>
          <small>{game.competition.short_name}</small>
        </div>
      </div>
      <nav className="sidebar-nav">
        <NavGroup title="Club" links={primary} onNavigate={onNavigate} />
        <NavGroup title="Equipo" links={teamLinks} onNavigate={onNavigate} />
        <NavGroup title="Competición" links={links} onNavigate={onNavigate} />
        <NavGroup title="Gestión" links={clubLinks} onNavigate={onNavigate} />
      </nav>
      <div className="sidebar-footer">
        <div className="season-chip">
          <span>Temporada</span>
          <b>{game.game.season}</b>
          <small>J{game.game.round} · {shortLeague(game.competition.code)}</small>
        </div>
        <NavLink to="/game/options" className="nav-link" onClick={onNavigate}>
          <Settings size={17} />
          <span>Ajustes</span>
        </NavLink>
      </div>
    </aside>
  )
}

function Topbar({ onMenu }: { onMenu: () => void }) {
  const { game, refresh } = useGame()
  const { toast } = useToast()
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  if (!game) return null
  const saveName = game.game.save_name

  async function save() {
    setSaving(true)
    try {
      const { data } = await api.post<GameState>('/save', { name: saveName })
      toast('Partida guardada.', 'success')
      if (data) await refresh()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo guardar.', 'danger')
    } finally {
      setSaving(false)
    }
  }

  async function exit() {
    try {
      await api.post('/exit')
      navigate('/', { replace: true })
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo salir.', 'danger')
    }
  }

  return (
    <header className="topbar">
      <button className="icon-btn mobile-only" onClick={onMenu} aria-label="Abrir menú">
        <Menu size={20} />
      </button>
      <div className="topbar-context">
        <Crest src={game.team.crest} name={game.team.name} size={28} />
        <span>{game.team.name}</span>
        <ChevronRight size={14} />
        <b>{game.competition.short_name}</b>
        <span className="topbar-dot">·</span>
        <span>{game.game.phase === 'season_end' ? 'Fin de temporada' : game.game.phase === 'promotion' ? `Fase de ascenso · J${game.game.promotion_round || 1}` : `Jornada ${game.game.round}`}</span>
        <span className="topbar-dot">·</span>
        <span>{dateLabel(game.game.date)}</span>
      </div>
      <div className="topbar-actions">
        {game.game.live_active && <Badge tone="danger">En directo</Badge>}
        <span className="save-name" title={game.game.save_name}>{game.game.save_name}</span>
        <button className="icon-btn" onClick={() => navigate('/saves')} aria-label="Gestionar partidas guardadas" title="Gestionar partidas guardadas">
          <FolderOpen size={18} />
        </button>
        <button className="icon-btn" onClick={save} aria-label="Guardar" title="Guardar partida" disabled={saving}>
          <Save size={18} className={saving ? 'spin' : ''} />
        </button>
        <button className="icon-btn" onClick={exit} aria-label="Salir" title="Salir de la partida">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  )
}

function MobileNav({ onMore }: { onMore: () => void }) {
  return (
    <nav className="mobile-nav">
      <NavLink to="/game" end className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}>
        <LayoutDashboard size={19} />
        <span>Inicio</span>
      </NavLink>
      <NavLink to="/game/squad" className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}>
        <Users size={19} />
        <span>Plantilla</span>
      </NavLink>
      <NavLink to="/game/match" className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}>
        <Flag size={19} />
        <span>Partido</span>
      </NavLink>
      <NavLink to="/game/market" className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}>
        <ArrowLeftRight size={19} />
        <span>Mercado</span>
      </NavLink>
      <button type="button" className="mobile-nav-link" onClick={onMore}>
        <Menu size={19} />
        <span>Más</span>
      </button>
    </nav>
  )
}

export function GameLayout() {
  const { game, loading, error } = useGame()
  const [drawer, setDrawer] = useState(false)
  const location = useLocation()

  if (loading) {
    return (
      <div className="app-loading">
        <Logo />
        <LoadingBlock label="Cargando club, plantilla y competición…" />
      </div>
    )
  }

  if (error || !game) {
    return (
      <div className="app-loading">
        <Logo />
        <div className="notice notice-danger">{error || 'No se pudo cargar la partida.'}</div>
        <Button variant="primary" onClick={() => window.location.reload()}>Reintentar</Button>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <Topbar onMenu={() => setDrawer(true)} />
        <main className="app-content" id="main">
          <Outlet />
        </main>
      </div>
      <MobileNav onMore={() => setDrawer(true)} />
      {drawer && (
        <div className="drawer-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setDrawer(false)}>
          <div className="drawer">
            <div className="drawer-head">
              <Logo />
              <button className="icon-btn" onClick={() => setDrawer(false)} aria-label="Cerrar menú">
                <X size={18} />
              </button>
            </div>
            <div className="drawer-body">
              <Sidebar onNavigate={() => setDrawer(false)} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
