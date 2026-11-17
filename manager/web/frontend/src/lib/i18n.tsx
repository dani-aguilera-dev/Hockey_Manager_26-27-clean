import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

export type Lang = 'es' | 'en'

const STORAGE_KEY = 'hm_lang'

const EN: Record<string, string> = {
  Club: 'Club',
  Equipo: 'Squad',
  Competición: 'Competition',
  Gestión: 'Management',
  Dashboard: 'Dashboard',
  Decisiones: 'Decisions',
  Actualidad: 'News',
  Vestuario: 'Dressing room',
  'Reunión de equipo': 'Team meeting',
  Plantilla: 'Squad',
  Táctica: 'Tactics',
  'Planes de partido': 'Match plans',
  Entrenamiento: 'Training',
  Desarrollo: 'Development',
  Enfermería: 'Medical',
  'Calendario y amistosos': 'Calendar & friendlies',
  'Próximo partido': 'Next match',
  'Data hub rival': 'Opposition data hub',
  'Análisis de partido': 'Match analysis',
  Clasificación: 'Table',
  Premios: 'Awards',
  Objetivos: 'Objectives',
  'Copa del Rey': 'Copa del Rey',
  'Europa · EHL': 'Europe · EHL',
  Mercado: 'Transfer market',
  Seguimiento: 'Shortlist',
  Pruebas: 'Trials',
  'Comparar jugadores': 'Compare players',
  Contratos: 'Contracts',
  Cláusulas: 'Release clauses',
  Ojeo: 'Scouting',
  Cesiones: 'Loans',
  'Comercial y marca': 'Commercial & brand',
  Finanzas: 'Finance',
  Staff: 'Staff',
  Responsabilidades: 'Responsibilities',
  'Junta y visión': 'Board & vision',
  'Perfil del mánager': 'Manager profile',
  'Trabajo y seguridad': 'Job security',
  Vacantes: 'Vacancies',
  Instalaciones: 'Facilities',
  Cantera: 'Youth academy',
  'Afiliados y mentoring': 'Affiliates & mentoring',
  Historial: 'History',
  Prensa: 'Press',
  'Fase de ascenso': 'Promotion phase',
  Temporada: 'Season',
  Ajustes: 'Settings',
  Inicio: 'Home',
  Partido: 'Match',
  Más: 'More',
  Guardar: 'Save',
  Salir: 'Exit',
  'Guardar partida': 'Save game',
  'Gestionar partidas guardadas': 'Manage saves',
  'Abrir menú': 'Open menu',
  'En directo': 'Live',
  'Fin de temporada': 'End of season',
  Jornada: 'Matchday',
  'Saltar al contenido': 'Skip to content',
  'Primeros pasos': 'Getting started',
  'Tu primera semana': 'Your first week',
  'Ocultar guía': 'Hide guide',
  'Revisa la plantilla': 'Review the squad',
  'Fichas, posición y disponibilidad.': 'Profiles, positions and availability.',
  'Ajusta la táctica': 'Adjust tactics',
  'Formación, presión y roles de PC.': 'Formation, pressing and PC roles.',
  'Planifica el entrenamiento': 'Plan training',
  'Carga, moral y preparación del rival.': 'Load, morale and opponent preparation.',
  'Prepara el partido': 'Prepare the match',
  'Once, previa y decisión de jugar.': 'Lineup, preview and match decision.',
  'Idioma / Language': 'Language',
  'Interfaz de navegación y guía inicial. El contenido editorial sigue en español.':
    'Navigation shell and onboarding. Editorial content remains in Spanish.',
}

interface LanguageValue {
  lang: Lang
  setLang: (lang: Lang) => void
  t: (text: string) => string
}

const LanguageContext = createContext<LanguageValue | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'en' ? 'en' : 'es'
    } catch {
      return 'es'
    }
  })

  useEffect(() => {
    document.documentElement.lang = lang
    try {
      localStorage.setItem(STORAGE_KEY, lang)
    } catch {
      // Sin persistencia si el navegador bloquea localStorage.
    }
  }, [lang])

  const t = useCallback((text: string) => (lang === 'en' ? EN[text] ?? text : text), [lang])

  return <LanguageContext.Provider value={{ lang, setLang, t }}>{children}</LanguageContext.Provider>
}

export function useLanguage(): LanguageValue {
  const value = useContext(LanguageContext)
  if (!value) throw new Error('useLanguage debe usarse dentro de LanguageProvider')
  return value
}
