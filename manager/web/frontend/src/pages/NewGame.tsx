import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Search } from 'lucide-react'
import { api } from '../lib/api'
import type { ClubCard, LeagueGroup, NewGameCatalog } from '../types'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Crest, LoadingBlock, Logo } from '../components/ui'

const COUNTRY_ORDER = ['España', 'Países Bajos', 'Bélgica', 'Alemania', 'Inglaterra', 'Argentina', 'India']

const COUNTRY_LOGOS: Record<string, string> = {
  España: 'es',
  'Países Bajos': 'nl',
  Bélgica: 'be',
  Alemania: 'de',
  Inglaterra: 'gb-eng',
  Argentina: 'ar',
  India: 'in',
}

const LEAGUE_LOGOS: Record<string, string> = {
  DHA: 'es',
  DHB: 'es',
  '1A': 'es-an',
  '1N': 'es-pv',
  '1M': 'es-md',
  '1G': 'es-ga',
  '1C': 'es-cn',
  '1V': 'es-vc',
  SUP: 'es-ct',
  CAT1: 'es-ct',
  NED: 'nl',
  BEL: 'be',
  GER: 'de',
  ENG: 'gb-eng',
  ARG: 'ar',
  IND: 'in',
}

type CountryGroup = {
  country: string
  countryCode: string
  leagues: LeagueGroup[]
}

function logoForCountry(country: string) {
  return `/static/league-logos/${COUNTRY_LOGOS[country] || 'es'}.png`
}

function logoForLeague(code: string) {
  return `/static/league-logos/${LEAGUE_LOGOS[code] || 'es'}.png`
}

export default function NewGame() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [catalog, setCatalog] = useState<NewGameCatalog | null>(null)
  const [loading, setLoading] = useState(true)
  const [country, setCountry] = useState('España')
  const [leagueCode, setLeagueCode] = useState('')
  const [clubId, setClubId] = useState('')
  const [search, setSearch] = useState('')
  const [manager, setManager] = useState('Entrenador')
  const [seed, setSeed] = useState('')
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    api.get<NewGameCatalog>('/new-game')
      .then(({ data }) => {
        setCatalog(data)
        const first = data.leagues[0]
        if (first) {
          setCountry(first.competition.country)
          setLeagueCode(first.competition.code)
          setClubId(first.clubs[0]?.id || '')
        }
      })
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el catálogo.', 'danger'))
      .finally(() => setLoading(false))
  }, [toast])

  const countryGroups = useMemo<CountryGroup[]>(() => {
    const groups = new Map<string, CountryGroup>()
    for (const group of catalog?.leagues || []) {
      const name = group.competition.country
      if (!groups.has(name)) {
        groups.set(name, { country: name, countryCode: group.competition.country_code, leagues: [] })
      }
      groups.get(name)!.leagues.push(group)
    }
    return [...groups.values()].sort((a, b) => {
      const ai = COUNTRY_ORDER.indexOf(a.country)
      const bi = COUNTRY_ORDER.indexOf(b.country)
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi) || a.country.localeCompare(b.country)
    })
  }, [catalog])

  const currentCountry = useMemo(
    () => countryGroups.find((group) => group.country === country) || countryGroups[0],
    [countryGroups, country],
  )
  const countryLeagues = currentCountry?.leagues || []
  const league: LeagueGroup | undefined = useMemo(
    () => countryLeagues.find((item) => item.competition.code === leagueCode) || countryLeagues[0],
    [countryLeagues, leagueCode],
  )

  const clubs: ClubCard[] = useMemo(() => {
    const list = league?.clubs || []
    const needle = search.trim().toLowerCase()
    if (!needle) return list
    return list.filter((club) =>
      [club.name, club.city, club.stadium, club.board_expectation].some((value) => value.toLowerCase().includes(needle)),
    )
  }, [league, search])

  const selected = useMemo(
    () => (league?.clubs || []).find((club) => club.id === clubId) || null,
    [league, clubId],
  )

  function chooseCountry(group: CountryGroup) {
    setCountry(group.country)
    const first = group.leagues[0]
    setLeagueCode(first?.competition.code || '')
    setClubId(first?.clubs[0]?.id || '')
    setSearch('')
  }

  function chooseLeague(group: LeagueGroup) {
    setLeagueCode(group.competition.code)
    setClubId(group.clubs[0]?.id || '')
    setSearch('')
  }

  async function start() {
    if (!selected) return
    setStarting(true)
    try {
      await api.post('/new-game', { club_id: selected.id, manager, seed })
      navigate('/game')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo crear la partida.', 'danger')
    } finally {
      setStarting(false)
    }
  }

  if (loading) {
    return <div className="app-loading"><Logo /><LoadingBlock label="Cargando países, competiciones y clubes…" /></div>
  }

  return (
    <div className="newgame-page">
      <div className="newgame-inner">
        <div className="newgame-top">
          <Logo />
          <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate('/')}>Volver al inicio</Button>
        </div>

        <div className="newgame-heading">
          <div>
            <div className="eyebrow">Nueva partida · Paso 2 de 3</div>
            <h1>Elige país, división y club.</h1>
            <p>Filtra por país, entra en la división y escoge tu próximo proyecto.</p>
          </div>
          <label className="search-box">
            <Search size={16} />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar club o ciudad…" aria-label="Buscar club" />
          </label>
        </div>

        <div className="selector-label">País</div>
        <div className="country-tabs" role="tablist" aria-label="Países">
          {countryGroups.map((group) => (
            <button
              key={group.country}
              type="button"
              role="tab"
              aria-selected={group.country === currentCountry?.country}
              className={`country-tab ${group.country === currentCountry?.country ? 'active' : ''}`}
              onClick={() => chooseCountry(group)}
            >
              <img src={logoForCountry(group.country)} alt="" />
              <span>
                <b>{group.country}</b>
                <small>{group.leagues.length} {group.leagues.length === 1 ? 'división' : 'divisiones'}</small>
              </span>
            </button>
          ))}
        </div>

        <div className="selector-label">Divisiones · {currentCountry?.country}</div>
        <div className="league-tabs" role="tablist" aria-label="Divisiones">
          {countryLeagues.map((group) => (
            <button
              key={group.competition.code}
              type="button"
              role="tab"
              aria-selected={group.competition.code === league?.competition.code}
              className={`league-tab ${group.competition.code === league?.competition.code ? 'active' : ''}`}
              onClick={() => chooseLeague(group)}
            >
              <img className="league-tab-logo" src={logoForLeague(group.competition.code)} alt="" />
              <span className="league-tab-copy">
                <small>{group.competition.country.toUpperCase()}</small>
                <b>{group.competition.short_name}</b>
                <span>{group.clubs.length} clubes · nivel {group.competition.standard}</span>
              </span>
            </button>
          ))}
        </div>

        {league && (
          <div className="league-banner">
            <div className="league-banner-mark">
              <img src={logoForLeague(league.competition.code)} alt="" />
            </div>
            <div className="league-banner-main">
              <div className="eyebrow">{league.competition.name}</div>
              <h2>{league.competition.country} · {league.competition.confederation}</h2>
              <p>{league.clubs.length} clubes · {league.competition.format.replaceAll('_', ' ')} · nivel de referencia {league.competition.standard}</p>
            </div>
            <Badge tone="gold">Nivel {league.competition.standard}</Badge>
          </div>
        )}

        <div className="club-grid">
          {clubs.map((club) => (
            <button
              key={club.id}
              type="button"
              className={`club-card ${club.id === clubId ? 'selected' : ''}`}
              onClick={() => setClubId(club.id)}
            >
              <Crest src={club.crest} name={club.name} size={44} />
              <div className="club-card-main">
                <b>{club.name}</b>
                <span>{club.city} · {club.stadium}</span>
                <small>{club.expectation || club.board_expectation} · {club.difficulty}</small>
              </div>
              {club.id === clubId && <Badge tone="gold">Elegido</Badge>}
            </button>
          ))}
        </div>
        {!clubs.length && <div className="club-grid-empty">No hay clubes que coincidan con la búsqueda.</div>}

        <div className="form-row mt-2" style={{ maxWidth: 560 }}>
          <label className="field">
            <span>Nombre del entrenador</span>
            <input value={manager} onChange={(event) => setManager(event.target.value)} maxLength={40} />
          </label>
          <label className="field">
            <span>Semilla opcional</span>
            <input value={seed} onChange={(event) => setSeed(event.target.value.replace(/\D/g, ''))} placeholder="Aleatoria" inputMode="numeric" />
          </label>
        </div>
      </div>

      <div className="selected-bar">
        <Crest src={selected?.crest} name={selected?.name || 'Club'} size={42} />
        <div className="selected-bar-main">
          <span>CLUB SELECCIONADO</span>
          <b>{selected ? `${selected.name} · ${selected.country}` : 'Elige un club'}</b>
          <small>{selected ? `${selected.city} · ${selected.stadium} · ${selected.expectation}` : 'Selecciona una tarjeta para continuar'}</small>
        </div>
        <Button variant="primary" size="lg" icon={ArrowRight} onClick={start} disabled={!selected} loading={starting}>
          Empezar partida
        </Button>
      </div>
    </div>
  )
}
