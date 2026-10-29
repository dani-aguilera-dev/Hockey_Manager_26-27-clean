-- Hockey Manager España 2026-27
-- Esquema SQLite de referencia. Los campos JSON se guardan como TEXT y se consultan con json_extract().
PRAGMA foreign_keys = ON;

-- =========================================================
-- 1. SAVE / META
-- =========================================================
CREATE TABLE saves (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  manager_name TEXT NOT NULL,
  club_id TEXT NOT NULL,
  season TEXT NOT NULL,
  seed INTEGER NOT NULL,
  difficulty TEXT NOT NULL DEFAULT 'normal',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  version TEXT NOT NULL
);

-- =========================================================
-- 2. CLUBES, ESTADIOS, CIUDADES
-- =========================================================
CREATE TABLE clubs (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  full_name TEXT NOT NULL,
  league TEXT NOT NULL,
  city_id TEXT NOT NULL,
  community TEXT,
  province TEXT,
  founded INTEGER,
  colors_json TEXT,
  nickname TEXT,
  history TEXT,
  data_quality TEXT DEFAULT 'media',
  reputation INTEGER DEFAULT 50,
  fanbase INTEGER DEFAULT 1000
);

CREATE TABLE cities (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  community TEXT,
  province TEXT,
  country TEXT DEFAULT 'España',
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  airport TEXT,
  airport_name TEXT,
  train TEXT,
  timezone TEXT DEFAULT 'Europe/Madrid'
);

CREATE TABLE stadiums (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  name TEXT NOT NULL,
  address TEXT,
  city_id TEXT REFERENCES cities(id),
  surface TEXT,              -- water-based, sand-dressed, sand-filled, natural
  capacity INTEGER,
  capacity_confidence TEXT,  -- oficial, estimada, desconocida
  notes TEXT
);

CREATE TABLE facilities (
  club_id TEXT PRIMARY KEY REFERENCES clubs(id),
  pitches INTEGER DEFAULT 1,
  gym INTEGER DEFAULT 1,
  medical INTEGER DEFAULT 1,
  video INTEGER DEFAULT 0,
  academy INTEGER DEFAULT 3,  -- 1-5
  confidence TEXT DEFAULT 'modelo'
);

CREATE TABLE rivalries (
  club_id TEXT NOT NULL REFERENCES clubs(id),
  rival_id TEXT NOT NULL REFERENCES clubs(id),
  intensity INTEGER DEFAULT 3, -- 1-5
  notes TEXT,
  PRIMARY KEY (club_id, rival_id)
);

-- =========================================================
-- 3. COMPETICIONES Y CALENDARIO
-- =========================================================
CREATE TABLE competitions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  level INTEGER NOT NULL,
  format_json TEXT NOT NULL,
  parent_id TEXT REFERENCES competitions(id)
);

CREATE TABLE seasons (
  id TEXT PRIMARY KEY,
  competition_id TEXT NOT NULL REFERENCES competitions(id),
  name TEXT NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  status TEXT DEFAULT 'pending'
);

CREATE TABLE season_teams (
  season_id TEXT NOT NULL REFERENCES seasons(id),
  club_id TEXT NOT NULL REFERENCES clubs(id),
  group_id TEXT,
  PRIMARY KEY (season_id, club_id)
);

CREATE TABLE fixtures (
  id TEXT PRIMARY KEY,
  season_id TEXT NOT NULL REFERENCES seasons(id),
  round INTEGER,
  phase TEXT,                -- regular, final4, playout, promotion, relegation
  date TEXT NOT NULL,
  time TEXT,
  home_club_id TEXT NOT NULL REFERENCES clubs(id),
  away_club_id TEXT NOT NULL REFERENCES clubs(id),
  stadium_id INTEGER REFERENCES stadiums(id),
  status TEXT DEFAULT 'scheduled', -- scheduled, played, postponed, cancelled
  home_goals INTEGER,
  away_goals INTEGER,
  attendance INTEGER,
  weather_json TEXT,
  pitch_condition TEXT,
  notes TEXT
);

CREATE TABLE standings (
  season_id TEXT NOT NULL REFERENCES seasons(id),
  club_id TEXT NOT NULL REFERENCES clubs(id),
  group_id TEXT,
  played INTEGER DEFAULT 0,
  won INTEGER DEFAULT 0,
  drawn INTEGER DEFAULT 0,
  lost INTEGER DEFAULT 0,
  goals_for INTEGER DEFAULT 0,
  goals_against INTEGER DEFAULT 0,
  points INTEGER DEFAULT 0,
  position INTEGER,
  form TEXT,
  PRIMARY KEY (season_id, club_id)
);

-- =========================================================
-- 4. JUGADORES Y ATRIBUTOS
-- =========================================================
CREATE TABLE players (
  id TEXT PRIMARY KEY,
  club_id TEXT REFERENCES clubs(id),
  name TEXT NOT NULL,
  birth_date TEXT,
  age INTEGER,
  nationality TEXT DEFAULT 'España',
  position_group TEXT,       -- Portero, Defensa, Medio, Delantero, Polivalente
  subposition TEXT,          -- Portero, Central, Lateral, Medio, Delantero, Polivalente
  height_cm INTEGER,
  weight_kg INTEGER,
  preferred_side TEXT,       -- derecha, revés, ambas
  profile TEXT DEFAULT 'Jugador', -- Jugador, Invitado
  status TEXT DEFAULT 'activo',   -- activo, lesionado, sancionado, baja
  attributes_json TEXT NOT NULL,  -- 37 atributos
  overalls_json TEXT NOT NULL,    -- 5 overalls
  overall REAL,
  potential REAL,
  value INTEGER,
  polivalencia REAL,
  archetype TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE contracts (
  id TEXT PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES players(id),
  club_id TEXT NOT NULL REFERENCES clubs(id),
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  wage INTEGER NOT NULL,
  signing_bonus INTEGER DEFAULT 0,
  release_clause INTEGER,
  squad_role TEXT,           -- estrella, titular, rotación, promesa, cantera
  bonuses_json TEXT,
  status TEXT DEFAULT 'active'
);

-- =========================================================
-- 5. CUERPO TÉCNICO
-- =========================================================
CREATE TABLE staff_roles (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  effects_json TEXT,
  key_attributes_json TEXT
);

CREATE TABLE staff (
  id TEXT PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  role_id TEXT NOT NULL REFERENCES staff_roles(id),
  name TEXT NOT NULL,
  age INTEGER,
  attributes_json TEXT,
  wage INTEGER,
  contract_end TEXT,
  status TEXT DEFAULT 'active'
);

-- =========================================================
-- 6. TÁCTICA Y ALINEACIONES
-- =========================================================
CREATE TABLE tactics (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  name TEXT NOT NULL,
  formation TEXT NOT NULL,
  mentality TEXT DEFAULT 'equilibrada',
  press TEXT DEFAULT 'media',
  block TEXT DEFAULT 'medio',
  width TEXT DEFAULT 'normal',
  tempo TEXT DEFAULT 'normal',
  passing TEXT DEFAULT 'mixto',
  pc_routine TEXT DEFAULT 'directa',
  instructions_json TEXT,
  set_piece_roles_json TEXT, -- injector, stopper, flicker, deflector, first_runner, gk, stroke_taker, stroke_gk
  is_default INTEGER DEFAULT 1
);

CREATE TABLE lineups (
  id INTEGER PRIMARY KEY,
  fixture_id TEXT NOT NULL REFERENCES fixtures(id),
  club_id TEXT NOT NULL REFERENCES clubs(id),
  player_id TEXT NOT NULL REFERENCES players(id),
  slot TEXT NOT NULL,        -- GK, CEN, LAT, MED, DEL
  role TEXT,
  starting INTEGER DEFAULT 1,
  minutes INTEGER DEFAULT 0,
  rating REAL,
  UNIQUE (fixture_id, player_id)
);

-- =========================================================
-- 7. PARTIDO: EVENTOS Y ESTADÍSTICAS
-- =========================================================
CREATE TABLE match_events (
  id INTEGER PRIMARY KEY,
  fixture_id TEXT NOT NULL REFERENCES fixtures(id),
  minute INTEGER NOT NULL,
  second INTEGER DEFAULT 0,
  type TEXT NOT NULL,        -- goal, save, pc, stroke, card, injury, substitution, chance...
  club_id TEXT REFERENCES clubs(id),
  player_id TEXT REFERENCES players(id),
  assistant_id TEXT REFERENCES players(id),
  text TEXT NOT NULL,
  xg REAL,
  metadata_json TEXT
);

CREATE TABLE match_stats (
  fixture_id TEXT NOT NULL REFERENCES fixtures(id),
  club_id TEXT NOT NULL REFERENCES clubs(id),
  possession REAL,
  shots INTEGER DEFAULT 0,
  shots_on_target INTEGER DEFAULT 0,
  pc INTEGER DEFAULT 0,
  pc_goals INTEGER DEFAULT 0,
  strokes INTEGER DEFAULT 0,
  stroke_goals INTEGER DEFAULT 0,
  saves INTEGER DEFAULT 0,
  green_cards INTEGER DEFAULT 0,
  yellow_cards INTEGER DEFAULT 0,
  red_cards INTEGER DEFAULT 0,
  circle_entries INTEGER DEFAULT 0,
  tackles INTEGER DEFAULT 0,
  interceptions INTEGER DEFAULT 0,
  aerials INTEGER DEFAULT 0,
  passes INTEGER DEFAULT 0,
  pass_completion REAL,
  PRIMARY KEY (fixture_id, club_id)
);

CREATE TABLE player_match_stats (
  fixture_id TEXT NOT NULL REFERENCES fixtures(id),
  player_id TEXT NOT NULL REFERENCES players(id),
  minutes INTEGER DEFAULT 0,
  goals INTEGER DEFAULT 0,
  assists INTEGER DEFAULT 0,
  shots INTEGER DEFAULT 0,
  pc_goals INTEGER DEFAULT 0,
  saves INTEGER DEFAULT 0,
  green_cards INTEGER DEFAULT 0,
  yellow_cards INTEGER DEFAULT 0,
  red_cards INTEGER DEFAULT 0,
  rating REAL,
  distance_km REAL,
  PRIMARY KEY (fixture_id, player_id)
);

-- =========================================================
-- 8. SALUD, MORAL, DINÁMICA
-- =========================================================
CREATE TABLE injuries (
  id INTEGER PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES players(id),
  type TEXT NOT NULL,
  severity TEXT,             -- leve, moderada, grave
  start_date TEXT NOT NULL,
  end_date TEXT,
  status TEXT DEFAULT 'activa',
  notes TEXT
);

CREATE TABLE suspensions (
  id INTEGER PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES players(id),
  reason TEXT NOT NULL,
  start_date TEXT NOT NULL,
  matches INTEGER NOT NULL,
  status TEXT DEFAULT 'activa'
);

CREATE TABLE morale (
  id INTEGER PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES players(id),
  date TEXT NOT NULL,
  morale INTEGER,            -- 1-20
  happiness INTEGER,         -- 1-20
  relationships_json TEXT,
  notes TEXT
);

CREATE TABLE squad_dynamics (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  date TEXT NOT NULL,
  cohesion INTEGER,
  determination INTEGER,
  leadership INTEGER,
  notes TEXT
);

-- =========================================================
-- 9. ENTRENAMIENTO Y DESARROLLO
-- =========================================================
CREATE TABLE training_sessions (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  date TEXT NOT NULL,
  type TEXT NOT NULL,        -- recuperación, físico, técnico, táctico, set pieces, vídeo, descanso
  intensity TEXT,            -- suave, media, alta
  focus TEXT,
  attendance_json TEXT,
  notes TEXT
);

CREATE TABLE training_plans (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  week_start TEXT NOT NULL,
  day_of_week INTEGER NOT NULL, -- 1-7
  session_type TEXT NOT NULL,
  intensity TEXT,
  focus TEXT
);

-- =========================================================
-- 10. FINANZAS
-- =========================================================
CREATE TABLE budgets (
  club_id TEXT NOT NULL REFERENCES clubs(id),
  season TEXT NOT NULL,
  transfer_budget INTEGER DEFAULT 0,
  wage_budget INTEGER DEFAULT 0,
  operational_budget INTEGER DEFAULT 0,
  balance INTEGER DEFAULT 0,
  currency TEXT DEFAULT 'EUR',
  confidence TEXT DEFAULT 'modelo',
  PRIMARY KEY (club_id, season)
);

CREATE TABLE transactions (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  date TEXT NOT NULL,
  type TEXT NOT NULL,        -- ingreso, gasto
  category TEXT NOT NULL,    -- taquilla, patrocinio, socios, salarios, viaje, hotel, fichaje, instalaciones
  amount INTEGER NOT NULL,
  description TEXT
);

CREATE TABLE travel_plans (
  id INTEGER PRIMARY KEY,
  fixture_id TEXT NOT NULL REFERENCES fixtures(id),
  club_id TEXT NOT NULL REFERENCES clubs(id),
  mode TEXT NOT NULL,        -- bus, tren, avión, barco, coche
  departure_date TEXT,
  return_date TEXT,
  distance_km REAL,
  travel_hours REAL,
  cost INTEGER,
  hotel_nights INTEGER DEFAULT 0,
  hotel_category TEXT,
  meals TEXT,
  fatigue_penalty REAL,
  training_loss INTEGER,
  notes TEXT
);

-- =========================================================
-- 11. MERCADO, OJEADORES, CANTERA
-- =========================================================
CREATE TABLE transfers (
  id INTEGER PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES players(id),
  from_club_id TEXT REFERENCES clubs(id),
  to_club_id TEXT REFERENCES clubs(id),
  fee INTEGER,
  date TEXT,
  window TEXT,               -- verano, invierno
  status TEXT DEFAULT 'pending',
  contract_id TEXT REFERENCES contracts(id)
);

CREATE TABLE transfer_offers (
  id INTEGER PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES players(id),
  from_club_id TEXT REFERENCES clubs(id),
  to_club_id TEXT REFERENCES clubs(id),
  fee INTEGER,
  wage INTEGER,
  status TEXT DEFAULT 'pending', -- pending, accepted, rejected, withdrawn
  date TEXT,
  response TEXT
);

CREATE TABLE scouting_assignments (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  scout_id TEXT REFERENCES staff(id),
  region TEXT,
  start_date TEXT,
  end_date TEXT,
  status TEXT DEFAULT 'active'
);

CREATE TABLE scouting_reports (
  id INTEGER PRIMARY KEY,
  player_id TEXT NOT NULL REFERENCES players(id),
  scout_id TEXT REFERENCES staff(id),
  date TEXT,
  knowledge INTEGER,         -- 0-100
  rating INTEGER,
  notes TEXT
);

CREATE TABLE youth_players (
  id TEXT PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  name TEXT NOT NULL,
  age INTEGER,
  potential REAL,
  attributes_json TEXT,
  status TEXT DEFAULT 'cantera'
);

-- =========================================================
-- 12. DIRECTIVA, AFICIÓN, PRENSA, INBOX
-- =========================================================
CREATE TABLE board_objectives (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  season TEXT NOT NULL,
  type TEXT NOT NULL,        -- liga, promoción, permanencia, copa, finanzas, cantera
  target TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  reward TEXT
);

CREATE TABLE board_confidence (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  date TEXT NOT NULL,
  confidence INTEGER,
  notes TEXT
);

CREATE TABLE fan_confidence (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  date TEXT NOT NULL,
  confidence INTEGER,
  notes TEXT
);

CREATE TABLE media_events (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL,
  club_id TEXT REFERENCES clubs(id),
  type TEXT,
  headline TEXT,
  body TEXT,
  choices_json TEXT,
  resolved INTEGER DEFAULT 0
);

CREATE TABLE inbox (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL,
  club_id TEXT REFERENCES clubs(id),
  category TEXT,
  subject TEXT NOT NULL,
  body TEXT,
  read INTEGER DEFAULT 0,
  action_required INTEGER DEFAULT 0
);

-- =========================================================
-- 13. HISTORIA Y RÉCORDS
-- =========================================================
CREATE TABLE season_history (
  id INTEGER PRIMARY KEY,
  season TEXT NOT NULL,
  competition_id TEXT NOT NULL REFERENCES competitions(id),
  champion_club_id TEXT REFERENCES clubs(id),
  runner_up_club_id TEXT REFERENCES clubs(id),
  promoted_json TEXT,
  relegated_json TEXT,
  notes TEXT
);

CREATE TABLE club_records (
  id INTEGER PRIMARY KEY,
  club_id TEXT NOT NULL REFERENCES clubs(id),
  record_type TEXT NOT NULL,
  value TEXT,
  player_id TEXT REFERENCES players(id),
  season TEXT,
  notes TEXT
);
