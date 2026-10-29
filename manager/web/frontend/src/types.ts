export interface ApiEnvelope<T> {
  ok: boolean
  data: T
  message?: string
  error?: string
  code?: string
}

export interface Competition {
  code: string
  name: string
  short_name: string
  country: string
  country_code: string
  confederation: string
  standard: number
  start_date: string
  teams: number
  format: string
  playoffs: number
  relegation: number
  international: boolean
}



export interface Player {
  id: string
  name: string
  team_name: string
  origin_team: string
  team_id: string | null
  position_group: string
  subposition: string
  age: number
  overall: number
  potential: number
  attributes: Record<string, number>
  overalls: Record<string, number>
  archetype: string
  perfil: string
  value: number
  fatigue: number
  morale: number
  relationship: number
  relationship_label: string
  absence_label: string
  available: boolean
  form: number
  injury: number
  injury_type: string
  injury_severity: string
  injury_started: string
  injury_expected: number
  injury_history: Array<Record<string, unknown>>
  suspension: number
  suspension_reason: string
  suspension_started: string
  card_history: Array<Record<string, unknown>>
  traits: string[]
  promises: Array<Record<string, unknown>>
  season_goals: number
  season_assists: number
  apps: number
  rating: number
  salary: number
  contract_until: string
  league: string
  league_label: string
  photo: string
  photo_remote: string
  initials: string
  stars: string
  stars_bar: string
  tier: string
  youth_category: string
  career: CareerRow[]
  transfer_listed: boolean
  transfer_asking_price: number
  brand_deal?: BrandDeal
}

export interface CareerRow {
  season: string
  club: string
  league: string
  apps: number
  goals: number
  assists: number
  rating: number
  overall: number
  partial?: boolean
}

export interface StaffMember {
  role: string
  role_label: string
  name: string
  rating: number
  salary: number
  contract_until: string
  source: string
  confidence: string
  relationship: number
  relationship_label: string
  morale: number
}

export interface BoardMember {
  role: string
  name: string
  source: string
  confidence: string
}

export interface Tactics {
  formation: string
  mentality: string
  press: string
  block: string
  width: string
  tempo: string
  passing: string
  pc_routine: string
  defensive_system: string
  attack_system: string
  outlet: string
  press_trigger: string
  pc_injector_id: string
  pc_stopper_id: string
  pc_flicker_id: string
  pc_deflector_id: string
  pc_rebounder_id: string
  pc_first_runner_id: string
  pc_goalkeeper_id: string
  stroke_taker_id: string
  stroke_goalkeeper_id: string
  free_hit_taker_id: string
}

export interface TeamSummary {
  id: string
  name: string
  league: string
  city: string
  community: string
  country: string
  stadium_name: string
  stadium_capacity: number
  board_expectation: string
  points: number
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  position: number | null
  crest: string
  morale: number
  cohesion: number
}

export interface Team extends TeamSummary {
  tactics: Tactics
  budget: number
  transfer_budget: number
  wage_budget: number
  brand_rating: number
  ticket_price: number
  merchandising: number
  sponsor_deals: SponsorDeal[]
  commercial_history: CommercialHistory[]
  board_confidence: number
  fan_confidence: number
  manager_rating: number
  assistant_rating: number
  academy_rating: number
  board_pressure: string
  board_patience: number
  prep_bonus: number
  media_confidence: number
  equipment_bonus: number
  equipment_deals: BrandDeal[]
  management_score: number
  player_wage_bill: number
  staff_wage_bill: number
  players: Player[]
  staff: StaffMember[]
  board: BoardMember[]
  youth: Player[]
}

export interface Fixture {
  id: string
  round: number
  date: string
  phase: string
  played: boolean
  home_id: string
  away_id: string
  home_name: string
  away_name: string
  home_crest: string
  away_crest: string
  home_goals: number
  away_goals: number
  home_stats: Record<string, number>
  away_stats: Record<string, number>
  events: MatchEvent[]
  attendance: number
  travel: Record<string, unknown>
  label: string
  is_cup: boolean
}

export interface MatchEvent {
  minute: number
  quarter?: number
  type: string
  team_id?: string | null
  team_name?: string | null
  player_id?: string | null
  player_name?: string | null
  text: string
  score?: string
}

export interface Award {
  id: string
  label: string
  player_id: string
  player_name: string
  team_id: string
  team_name: string
  team_crest?: string
  team_position?: number
  photo?: string
  metric: string
  value: number
  goals: number
  assists: number
}

export interface NewsItem {
  id?: string
  category: string
  headline: string
  body: string
  summary?: string
  date: string
  hot?: boolean
  importance?: number
  crest_id?: string
  crest_id2?: string
  crest?: string
  crest2?: string
  photo?: string
  photo_url?: string
  team_ids?: string[]
  player_ids?: string[]
  awards?: Award[]
  stats?: Record<string, string | number>
  tags?: string[]
  related_players?: Player[]
  related_teams?: TeamSummary[]
}

export interface InboxItem {
  date: string
  from: string
  subject: string
  body: string
}

export interface DailyEvent {
  category: string
  headline: string
  body: string
  date: string
  league?: string
}

export interface DecisionChoice {
  id: string
  label: string
  description: string
  tone: string
}

export interface PendingDecision {
  id: string
  event_id: string
  category: string
  kind: string
  priority: number
  title: string
  body: string
  date: string
  expires_at: string
  choices: DecisionChoice[]
}

export interface EventHistoryItem {
  id: string
  event_id: string
  category: string
  title: string
  date: string
  status: string
  choice_label: string
  response: string
  resolved_at: string
}

export interface ChatTurn {
  speaker: 'player' | 'manager' | 'system'
  text: string
  date?: string
  headline?: string
  tone?: string
}

export interface ChatMessage {
  id: string
  player_id: string
  player_name: string
  date: string
  relationship: number
  text: string
  answered: boolean
  answer?: string
  response?: string
  options: ChatOption[]
  turns?: ChatTurn[]
  stage?: number
  max_stage?: number
  status?: string
  promise?: Record<string, unknown>
  target_type?: 'player' | 'staff'
  target_id?: string
  staff_role?: string
  target_name?: string
  target_role?: string
  target_photo?: string
  target_photo_url?: string
  target_initials?: string
  topic?: string
  topic_label?: string
  headline?: string
  tone?: string
  context?: {
    age?: number
    age_band?: string
    performance?: string
    role?: string
    form?: number
    apps?: number
    goals?: number
    contract_status?: string
    market_interest?: boolean
    team_position?: number
  }
}

export interface ChatOption {
  label: string
  effects: Record<string, number | string>
  response?: string
  headline?: string
  tone?: string
}

export interface ChatTarget {
  target_type: 'player' | 'staff'
  target_id: string
  name: string
  photo: string
  photo_remote?: string
  initials: string
  age?: number
  age_band?: string
  position?: string
  role?: string
  archetype?: string
  overall?: number
  potential?: number
  form?: number
  fatigue?: number
  morale: number
  relationship: number
  performance?: string
  status?: string
  contract_status?: string
  market_interest?: boolean
  team_position?: number
  team_name: string
  topic_count: number
  rating?: number
  salary?: number
  contract_until?: string
  apps?: number
  goals?: number
  assists?: number
}

export interface ChatTargets {
  players: ChatTarget[]
  staff: ChatTarget[]
}

export interface ChatTopic {
  id: string
  label: string
  description: string
  category: string
  recent?: boolean
  recommended?: boolean
}

export interface ChatPayload {
  messages: ChatMessage[]
  players: Record<string, Player>
  staff: Record<string, StaffMember>
  targets: ChatTargets
}

export interface ChatTopicsPayload {
  target: ChatTarget
  topics: ChatTopic[]
}

export interface Finance {
  cash: number
  transfer_budget: number
  brand_rating?: number
  brand_value?: number
  sponsor_annual?: number
  ticket_price?: number
  player_wage_bill: number
  staff_wage_bill: number
  annual_wage_bill: number
  round_player_wages: number
  round_staff_wages: number
  sponsor_round: number
  gate: number
  sponsor: number
  player_wages: number
  staff_wages: number
  travel: number
  income: number
  expenses: number
  net: number
  entries: FinanceEntry[]
}

export interface FinanceEntry {
  round: number
  gate: number
  sponsor: number
  player_wages: number
  staff_wages: number
  wages: number
  travel: number
  net: number
  cash_after: number
}

export interface CupData {
  active: boolean
  round: number
  status: string
  fixtures: Fixture[]
  next: Fixture | null
}

export interface EhlData {
  active?: boolean
  round?: number
  fixtures?: Array<{
    home: { id: string; name: string; country: string; strength: number }
    away: { id: string; name: string; country: string; strength: number }
    home_goals: number
    away_goals: number
    played: boolean
    winner_id: string
  }>
  winner_id?: string
  winner_name?: string
  participants?: string[]
  dates?: string[]
  results?: Array<{ round: number; label: string; fixtures: Array<{ home: string; away: string; home_goals: number; away_goals: number; winner: string }> }>
}

export interface GameMeta {
  manager_name: string
  club_id: string
  season: string
  round: number
  date: string
  competition: string
  country: string
  phase: string
  total_rounds: number
  save_name: string
  live_active: boolean
  week_trained: boolean
  dhb_group: string
  promotion_round?: number
}

export interface PromotionGroup {
  name: string
  leagues?: string[]
  team_ids: string[]
  teams?: TeamSummary[]
  table: Array<{ position: number; team_id: string; team: string; points: number; played: number; gd: number }>
  winner_id?: string
  winner?: string
  champion?: string
}

export interface PromotionObjective {
  key: 'league' | 'group' | 'final' | string
  title: string
  description: string
  status: 'pending' | 'active' | 'completed' | 'failed' | string
  detail: string
  state_text?: string
}

export interface PromotionLeaguePath {
  code: string
  name: string
  short_name: string
  spots: number
  qualifiers: Array<{ position: number; team_id: string; team: string; points: number }>
  table: Array<{ position: number; team_id: string; team: string; points: number }>
}

export interface PromotionPath {
  target: number
  position: number
  qualified: boolean
  leagues: PromotionLeaguePath[]
  objectives: PromotionObjective[]
}

export interface CompetitionObjectives {
  system: string
  title: string
  objectives: PromotionObjective[]
  path?: PromotionPath
}

export interface PromotionState {
  format?: string
  stage?: 'groups' | 'final'
  groups?: PromotionGroup[]
  final_group?: PromotionGroup | null
  qualified?: TeamSummary[]
  user_group?: string
  user_qualified?: boolean
  promoted_ids?: string[]
  champion_id?: string
  path?: PromotionPath
  leagues?: PromotionLeaguePath[]
}

export interface GameState {
  game: GameMeta
  competition: Competition
  team: Team
  promotion?: PromotionState
  objectives?: CompetitionObjectives
  table: TeamSummary[]
  fixtures: Fixture[]
  next_fixture: Fixture | null
  finance: Finance
  commercial: CommercialData
  news: NewsItem[]
  awards: Award[]
  inbox: InboxItem[]
  daily_events: DailyEvent[]
  decisions?: PendingDecision[]
  event_history?: EventHistoryItem[]
  chat_messages: ChatMessage[]
  press: { done: boolean; history: PressHistoryItem[]; post_available?: boolean; post_done?: boolean }
  market: { window: string; status: string; offers: IncomingOffer[]; history: MarketHistoryItem[]; negotiations?: Negotiation[] }
  cup: CupData
  ehl: EhlData
  ehl_next: string
  ehl_status: string
  last_result: MatchReport | null
  manual_lineup: string[]
  weekly_plan: string[]
  training_report: TrainingReport | null
  season_end: SeasonSummary | null
  saves: SaveEntry[]
  simulation?: { days: number; message?: string; stopped_at_match?: boolean; stopped_at_decision?: boolean; date?: string; events?: DailyEvent[] }
}

export interface PressHistoryItem {
  round: number
  kind?: 'pre' | 'post' | string
  question: string
  topic?: string
  answer: string
  headline: string
  opponent: string
  opponent_coach: string
  opponent_quote: string
  journalist?: string
  outlet?: string
  effects?: Record<string, number | string>
  media_confidence?: number
}

export interface NegotiationOffer {
  fee: number
  salary: number
  years: number
}

export interface NegotiationHistoryItem {
  round: number
  actor: string
  offer: NegotiationOffer
  message: string
  date: string
}

export interface Negotiation {
  id: string
  kind: 'buy' | 'renew' | string
  status: 'open' | 'accepted' | 'rejected' | 'walked' | 'pending_window' | string
  player_id: string
  player_name: string
  club_id?: string
  club_name: string
  round: number
  max_rounds: number
  patience: number
  offer: NegotiationOffer
  ask: NegotiationOffer
  counter?: NegotiationOffer
  message: string
  history: NegotiationHistoryItem[]
  created?: string
  updated?: string
}

export interface IncomingOffer {
  id: string
  player_id: string
  player_name: string
  from_club_id: string
  from_club_name: string
  from_league?: string
  fee: number
  salary: number
  years: number
  status?: string
  source?: string
  listed?: boolean
  buyer_budget?: number
  buyer_cash?: number
  expires?: string
}

export interface MarketHistoryItem {
  type: string
  round: number
  season: string
  player: string
  overall: number
  from: string
  to: string
  fee: number
  salary: number
}

export interface MatchReport {
  fixture_id: string
  round: number
  phase: string
  home_id: string
  home_name: string
  away_id: string
  away_name: string
  home_goals: number
  away_goals: number
  user_is_home: boolean
  user_goals: number
  user_against: number
  result: string
  events: MatchEvent[]
  home_stats: Record<string, number>
  away_stats: Record<string, number>
  user_stats: Record<string, number>
  ratings: Record<string, number>
  attendance: number
  travel: Record<string, unknown>
  home_management: Record<string, number>
  away_management: Record<string, number>
  prep_bonus: number
  shootout: Record<string, unknown>
  referee?: { name?: string; style?: string; strictness?: number; card_bias?: number }
  reviews?: MatchReview[]
  injuries?: MatchInjury[]
  cards?: MatchCard[]
  player_minutes?: Record<string, number>
  date: string
}

export interface MatchInjury {
  player_id: string
  player_name?: string
  team_id: string
  team_name?: string
  type?: string
  severity: string
  matches: number
  minute?: number
  quarter?: number
  date?: string
}

export interface MatchCard {
  player_id: string
  player_name?: string
  team_id: string
  team_name?: string
  type: 'green' | 'yellow' | 'red' | string
  label?: string
  duration_minutes?: number
  rest_of_match?: boolean
  minute?: number
  quarter?: number
  reason?: string
  suspension_matches?: number
  date?: string
}

export interface TrainingReport {
  message?: string
  fatigue_before?: number
  fatigue_after?: number
  morale_before?: number
  morale_after?: number
  prep_bonus?: number
  gains?: Array<{ player: string; attr: string }>
  injuries?: Array<{ player: string; matches: number }>
}

export interface SeasonSummary {
  competition: string
  champion?: string
  user_position: number
  table: Array<{ position: number; team: string; points: number; gd: number }>
  cup_winner?: string
  cup_third?: string
  ehl_winner?: string
  board_review?: {
    target: number
    position: number
    met: boolean
    confidence_before: number
    confidence_after: number
    message: string
  }
  promoted: string[]
  relegated: string[]
  playout?: Record<string, unknown>
  retirements: Array<{ player: string; club: string; age: number }>
}

export interface SaveEntry {
  id: number
  name: string
  club_id: string
  club_name: string
  crest: string
  season: string
  round: number
  updated_at: string
  is_current?: boolean
}

export interface MenuData {
  current: null | {
    team: TeamSummary
    competition: Competition
    season: string
    round: number
    date: string
    save_name: string
    live_active: boolean
  }
  saves: SaveEntry[]
}

export interface ClubCard extends TeamSummary {
  stadium: string
  expectation: string
  difficulty: string
}

export interface LeagueGroup {
  competition: Competition
  clubs: ClubCard[]
}

export interface NewGameCatalog {
  leagues: LeagueGroup[]
  clubs: ClubCard[]
  competitions: Competition[]
}

export interface Slot {
  index: number
  code: string
  group: string
  mismatch: boolean
  player: Player | null
}

export interface SlotRow {
  label: string
  slots: Slot[]
}

export interface TacticsPayload {
  tactics: Tactics
  line: Player[]
  bench: Player[]
  slots: string[]
  slot_rows: SlotRow[]
  slot_options: Player[][]
  available: Player[]
  squad: Player[]
  formations: string[]
  selected: string[]
}

export interface TrainingPayload {
  sessions: Record<string, { label: string; short: string; fatigue: number; attrs: string[] }>
  session_order: string[]
  days: string[]
  default_plan: string[]
  plan_name: string
  report: TrainingReport
  trained: boolean
  opponent: TeamSummary | null
  presets: Record<string, string[]>
}

export interface PressQuestion {
  id: string
  question: string
  topic?: string
  player_id: string
  options: Array<{ label: string; effects: Record<string, number | string>; headline: string }>
}

export interface PressPayload {
  questions: PressQuestion[]
  context: {
    rival: string
    rival_id?: string
    coach: string
    quote: string
    position?: number
    date: string
    journalist?: string
    outlet?: string
    style?: string
    bias?: string
    tone?: string
    media_confidence?: number
  }
  done: boolean
  post_available?: boolean
  history: PressHistoryItem[]
}

export interface PostPressPayload {
  questions: PressQuestion[]
  context: {
    fixture_id: string
    rival: string
    score: string
    result: string
    date: string
    journalist: string
    outlet: string
    style?: string
    bias?: string
    tone: string
    media_confidence: number
  }
  done: boolean
  available: boolean
  history: PressHistoryItem[]
}

export interface SponsorDeal {
  id: string
  name: string
  category: string
  category_id: string
  tier: string
  tier_label: string
  annual: number
  per_round: number
  years: number
  signing_bonus: number
  brand_boost: number
  requirement: string
  expires: string
  signed?: string
  end?: string
  active?: boolean
  status?: string
}

export interface SponsorOffer extends SponsorDeal {}

export interface BrandDeal {
  id: string
  brand_id?: string
  brand: string
  country?: string
  tier?: string
  tier_label?: string
  categories?: string[]
  annual: number
  per_round?: number
  signing_bonus?: number
  years?: number
  bonus?: number
  description?: string
  requirement?: string
  expires?: string
  signed?: string
  end?: string
  active?: boolean
  status?: string
}

export interface BrandOffer extends BrandDeal {}

export interface PlayerBrandOffer extends BrandDeal {
  player_id: string
  player_name: string
}

export interface BrandData {
  offers: BrandOffer[]
  player_offers: PlayerBrandOffer[]
  active_deals: BrandDeal[]
  player_deals: Array<BrandDeal & { player_id: string; player_name: string }>
  equipment_bonus: number
  brand_rating: number
  history: CommercialHistory[]
  brands: Array<{
    id: string
    name: string
    country: string
    categories: string[]
    tier: string
    base: number
    bonus: number
    description: string
  }>
}

export interface CommercialHistory {
  date: string
  type: string
  name: string
  annual: number
  bonus: number
  message: string
}

export interface CommercialCampaign {
  id: string
  label: string
  cost: number
  brand: number
  fan: number
  desc: string
  affordable: boolean
}

export interface CommercialData {
  brand_score: number
  brand_value: number
  brand_rating: number
  fan_confidence: number
  board_confidence: number
  ticket_price: number
  merchandising: number
  sponsor_round: number
  sponsor_annual: number
  merchandising_round: number
  ticket_estimate: number
  active_deals: SponsorDeal[]
  offers: SponsorOffer[]
  campaigns: CommercialCampaign[]
  history: CommercialHistory[]
  staff: Array<{ role: string; name: string; rating: number; salary: number; role_label: string }>
}

export interface MarketPlayer extends Player {
  owner: TeamSummary | null
  owner_name: string
  asking: number
  scout: string
  minimum_salary: number
  transfer_listed: boolean
  transfer_asking_price: number
  brand_deal?: BrandDeal
}

export interface ScoutRecommendation {
  player: MarketPlayer
  score: number
  reasons: string[]
  asking: number
  owner_name: string
  league: string
  league_name: string
  age: number
  overall: number
  potential: number
  salary: number
  rating: number
  apps: number
  goals: number
  assists: number
  affordable: boolean
  need_group: string
}

export interface ScoutData {
  scout: { name: string; rating: number; confidence: string; range: string }
  team_quality: number
  average_age: number
  transfer_budget: number
  wage_budget: number
  needs: Array<{ group: string; count: number; target: number; gap: number; quality: number; label: string }>
  focuses: Array<{ id: string; label: string }>
  focus: string
  recommendations: ScoutRecommendation[]
}

export interface MarketStaff {
  id: string
  role: string
  role_label: string
  name: string
  rating: number
  salary: number
  contract_until: string
  source: string
  confidence: string
  relationship: number
  morale: number
}

export interface MarketPayload {
  players: MarketPlayer[]
  free_agents: MarketPlayer[]
  staff: MarketStaff[]
  staff_roles: Record<string, string>
  teams: TeamSummary[]
  leagues: Array<{ code: string; name: string; short_name: string; country: string; standard: number }>
  attributes: string[]
  listed: Player[]
  own_players: Player[]
  pending_transfers: Array<{
    id: string
    type: 'compra' | 'venta'
    player_id: string
    player_name: string
    from_club_id: string
    to_club_id: string
    fee: number
    salary: number
    years: number
    status: string
    created: string
  }>
  window: string
  window_text: string
  offers: IncomingOffer[]
  negotiations?: Negotiation[]
  query: string
  max_value: number | null
  min_age: number | null
  max_age: number | null
  min_overall: number | null
  max_overall: number | null
  position: string
  club_id: string
  league: string
  attribute: string
  min_attribute: number | null
  listed_only: boolean
  free_agents_only: boolean
  total: number
  free_agent_total: number
  staff_total: number
}

export interface PlayerEditorData {
  position_groups: string[]
  subpositions: string[]
  player: {
    id: string
    name: string
    age: number
    position_group: string
    subposition: string
    archetype: string
    overall: number
    potential: number
    attributes: Record<string, number>
  }
}

export interface PlayerDetailPayload {
  player: Player
  owner: TeamSummary | null
  owner_name: string
  is_user: boolean
  editor?: PlayerEditorData
  market: null | {
    asking: number
    scout: string
    window: string
    window_text: string
    minimum_salary: number
  }
}

export interface FriendlyItem {
  id: string
  date: string
  home_id: string
  away_id: string
  home_name: string
  away_name: string
  home_goals: number
  away_goals: number
  played: boolean
  phase: string
  is_home: boolean
  notes?: string
}

export interface FriendlyCandidate {
  id: string
  name: string
  league: string
  league_name: string
  country: string
  city: string
  stadium_name: string
  overall: number
  crest: string
}

export interface FriendliesPayload {
  items: FriendlyItem[]
  dates: string[]
  candidates: FriendlyCandidate[]
  played: number
  pending: number
}

export interface CalendarPayload {
  friendlies: FriendliesPayload
  fixtures: Fixture[]
  next_fixture: Fixture | null
  next_friendly: FriendlyItem | null
  today: string
  season: string
  competition: Competition
}

export interface TeamDetailPayload {
  team: Team
  club: {
    history: string
    founded: string
    full_name: string
    city?: string
    province?: string
    community?: string
    country?: string
    source_url?: string
    location_verified?: boolean
    stadium: Record<string, unknown>
    colors: string[]
    facilities: Record<string, unknown>
  }
  position: number
  table: TeamSummary[]
  fixtures: Fixture[]
  played: Fixture[]
  upcoming: Fixture[]
  probable_lineup: Player[]
  probable_bench: Player[]
  probable_rows: SlotRow[]
  formation: string
  group: string
  is_user: boolean
}

export interface StaffPayload {
  team: Team
  staff_labels: Record<string, string>
  free_roles: string[]
}

export interface Candidate {
  role: string
  name: string
  rating: number
  salary: number
  contract_until: string
  source: string
  confidence: string
}

export interface StaffCandidatesPayload {
  role: string
  role_label: string
  candidates: Candidate[]
}

export interface YouthPayload {
  groups: Array<{
    category: string
    label: string
    ages: [number, number]
    players: Player[]
  }>
  team: Team
}

export interface MatchPreviewPayload {
  live: boolean
  fixture?: Fixture
  is_cup?: boolean
  home?: TeamSummary
  away?: TeamSummary
  line?: Player[]
  bench?: Player[]
  travel?: Array<{
    id: string
    label: string
    mode: string
    distance_km: number
    hours: number
    cost: number
    fatigue: number
    hotel_nights: number
    notes: string
  }>
  home_top?: Player | null
  away_top?: Player | null
  home_absences?: Player[]
  away_absences?: Player[]
  home_form?: string
  away_form?: string
  slot_rows?: SlotRow[]
  press_context?: PressPayload['context']
}

export interface LivePayload {
  fixture: Fixture
  user_side: number
  home: TeamSummary
  away: TeamSummary
  score: [number, number]
  quarter: number
  minute: number
  finished: boolean
  stats: { home: Record<string, number>; away: Record<string, number> }
  events: MatchEvent[]
  line: Player[]
  bench: Player[]
  player_rows: Array<{
    id: string
    name: string
    position: string
    minutes: number
    goals: number
    assists: number
    shots: number
    saves: number
    green: number
    yellow: number
    red: number
    rating: number
    fatigue: number
    injury: number
    suspension: number
  }>
  bench_rows: Array<{
    id: string
    name: string
    position: string
    overall: number
    fatigue: number
    form: number
    injury: number
    suspension: number
  }>
  tactics: Tactics
  travel: Record<string, unknown> | null
  snapshot: {
    quarter: number
    minute: number
    score: number[]
    finished: boolean
    home_stats: Record<string, number>
    away_stats: Record<string, number>
    home_management: Record<string, number>
    away_management: Record<string, number>
    home_tactical_bonus: number
    away_tactical_bonus: number
  }
  subs_left: number
  referrals: [number, number]
  last_decision: ReviewDecision | null
  reviews: MatchReview[]
}

export interface ReviewDecision {
  type: string
  label: string
  side: number
  team_name: string
  player_id?: string | null
  player_name?: string | null
  minute: number
  quarter: number
  score: string
  reviewed: boolean
  overturned?: boolean
  goal: boolean
  scorer_id?: string | null
  scorer_name?: string | null
  assister_id?: string | null
  goal_kind?: string
}

export interface MatchReview {
  minute: number
  quarter: number
  type: string
  label: string
  requested_by: string
  requested_side: number
  beneficiary: string
  overturned: boolean
  referrals_left: number
  score_before: string
  score_after: string
  text: string
}

export interface BoardFacility {
  id: string
  label: string
  value: number
}

export interface BoardRequestOption {
  id: string
  label: string
  description: string
  cost: number
  approval_chance: number
  available: boolean
  effect_text: string
  facility?: string
  delta?: number
  capacity?: number
  budget_gain?: number
  confidence?: number
}

export interface BoardHistoryEntry {
  date: string
  request_id: string
  label: string
  cost: number
  approved: boolean
  chance: number
  message: string
  before: Record<string, number | null>
  after: Record<string, number | null>
}

export interface BoardData {
  confidence: number
  fan_confidence: number
  patience: number
  pressure: string
  expectation: string
  manager_rating: number
  budget: number
  transfer_budget: number
  competition: {
    code: string
    name: string
    short_name: string
    position: number
    teams: number
  }
  stadium: { name: string; capacity: number }
  board_members: BoardMember[]
  vision: Array<{ horizon: string; goal: string; detail: string }>
  facilities: BoardFacility[]
  requests: BoardRequestOption[]
  history: BoardHistoryEntry[]
}

export interface LoanTarget {
  id: string
  name: string
  age: number
  position_group: string
  subposition: string
  overall: number
  potential: number
  team_id: string
  team_name: string
  league: string
  league_name: string
  salary: number
  value: number
  loan_fee: number
  wage_share_options: number[]
  playing_time_options: Array<{ id: string; label: string }>
  is_key: boolean
}

export interface LoanOutgoing extends LoanTarget {
  interested_clubs: Array<{
    id: string
    name: string
    league: string
    league_name: string
    squad_size: number
  }>
}

export interface ActiveLoan {
  id: string
  player_id: string
  player_name: string
  parent_club_id: string
  parent_club_name: string
  loan_club_id: string
  loan_club_name: string
  start_date: string
  end_date: string
  wage_share: number
  playing_time: string
  playing_time_label: string
  fee: number
  incoming: boolean
  is_incoming: boolean
  player_overall: number | null
  player_position: string
  player_age: number | null
  apps: number
  goals: number
  assists: number
}

export interface LoanHistoryEntry {
  date: string
  player_id: string
  player_name: string
  parent_club_id: string
  parent_club_name: string
  loan_club_id: string
  loan_club_name: string
  wage_share: number
  playing_time: string
  fee: number
  accepted: boolean
  chance: number
  direction: 'in' | 'out'
  message: string
  returned_on?: string
}

export interface LoansData {
  window: string
  window_text: string
  squad_size: number
  targets: LoanTarget[]
  outgoing: LoanOutgoing[]
  active: ActiveLoan[]
  history: LoanHistoryEntry[]
  playing_times: Array<{ id: string; label: string }>
}

export interface DatahubKeyPlayer {
  id: string
  name: string
  position: string
  position_group: string
  age: number
  overall: number
  goals: number
  assists: number
  rating: number
  apps: number
  status: string
  threat: string
  recommended_instruction: string
}

export interface DatahubInstructionOption {
  id: string
  label: string
  description: string
  attack: number
  defense: number
}

export interface DatahubTeamStats {
  played: number
  wins: number
  draws: number
  losses: number
  goals_for: number
  goals_against: number
  goals_per_game: number
  goals_against_per_game: number
  shots_per_game: number
  shots_on_target_per_game: number
  pc_per_game: number
  possession: number
  form: string
  position: number
}

export interface DatahubData {
  fixture: null | {
    id: string
    date: string
    round: number
    phase: string
    home_id: string
    away_id: string
    home_name: string
    away_name: string
    user_is_home: boolean
  }
  message?: string
  user_side?: number
  competition?: { code: string; name: string; short_name: string }
  user?: { id: string; name: string; stats: DatahubTeamStats; availability: Array<Record<string, unknown>> }
  opponent?: {
    id: string
    name: string
    league: string
    city: string
    stadium_name: string
    stats: DatahubTeamStats
    tactics: Tactics
    availability: Array<{ id: string; name: string; reason: string; injury: number; suspension: number }>
  }
  key_players?: DatahubKeyPlayer[]
  head_to_head?: Array<{ date: string; round: number; home_name: string; away_name: string; home_goals: number; away_goals: number }>
  analysis?: string[]
  options: DatahubInstructionOption[]
  instructions?: Record<string, string>
  recommended?: Record<string, string>
  effect?: { attack: number; defense: number; players: number }
}
