import { Route, Routes } from 'react-router-dom'
import { GameProvider } from './context/GameContext'
import { GameLayout } from './components/AppShell'
import MainMenu from './pages/MainMenu'
import NewGame from './pages/NewGame'
import LoadGame from './pages/LoadGame'
import SaveManager from './pages/SaveManager'
import Options from './pages/Options'
import Dashboard from './pages/Dashboard'
import CalendarPage from './pages/Calendar'
import BoardPage from './pages/Board'
import LoansPage from './pages/Loans'
import DataHubPage from './pages/DataHub'
import AffiliatesPage from './pages/Affiliates'
import HistoryPage from './pages/History'
import ScoutingPage from './pages/Scouting'
import TeamMeetingPage from './pages/TeamMeeting'
import FinancePage from './pages/Finance'
import AnalysisPage from './pages/Analysis'
import ResponsibilitiesPage from './pages/Responsibilities'
import DevelopmentPage from './pages/Development'
import AwardsPage from './pages/Awards'
import ContractsPage from './pages/Contracts'
import FacilitiesPage from './pages/Facilities'
import ClausesPage from './pages/Clauses'
import ShortlistPage from './pages/Shortlist'
import MatchPlansPage from './pages/MatchPlans'
import ManagerProfilePage from './pages/ManagerProfile'
import DecisionsPage from './pages/Decisions'
import Squad from './pages/Squad'
import PlayerPage from './pages/Player'
import TeamPage from './pages/Team'
import TacticsPage from './pages/Tactics'
import TrainingPage from './pages/Training'
import MedicalPage from './pages/Medical'
import MarketPage from './pages/Market'
import CommercialPage from './pages/Commercial'
import MarketPlayerPage from './pages/MarketPlayer'
import OffersPage from './pages/Offers'
import RenewPage from './pages/Renew'
import StaffPage from './pages/Staff'
import YouthPage from './pages/Youth'
import PressPage from './pages/Press'
import PostPressPage from './pages/PostPress'
import TablePage from './pages/Table'
import CupPage from './pages/Cup'
import EhlPage from './pages/Ehl'
import MatchPreview from './pages/MatchPreview'
import LiveMatch from './pages/LiveMatch'
import ReportPage from './pages/Report'
import NewsPage from './pages/News'
import ChatPage from './pages/Chat'
import SeasonEndPage from './pages/SeasonEnd'
import PromotionPage from './pages/Promotion'
import ObjectivesPage from './pages/Objectives'

function NotFound() {
  return (
    <div className="app-loading">
      <div className="eyebrow">404</div>
      <h1>Esta página no existe.</h1>
      <p className="muted">Vuelve al club o al menú principal.</p>
      <a className="btn btn-primary" href="/app/">Volver al inicio</a>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainMenu />} />
      <Route path="/new" element={<NewGame />} />
      <Route path="/load" element={<LoadGame />} />
      <Route path="/saves" element={<SaveManager />} />
      <Route path="/options" element={<Options />} />

      <Route
        path="/game"
        element={
          <GameProvider>
            <GameLayout />
          </GameProvider>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="board" element={<BoardPage />} />
        <Route path="loans" element={<LoansPage />} />
        <Route path="datahub" element={<DataHubPage />} />
        <Route path="affiliates" element={<AffiliatesPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="scouting" element={<ScoutingPage />} />
        <Route path="team-meeting" element={<TeamMeetingPage />} />
        <Route path="finance" element={<FinancePage />} />
        <Route path="analysis" element={<AnalysisPage />} />
        <Route path="responsibilities" element={<ResponsibilitiesPage />} />
        <Route path="development" element={<DevelopmentPage />} />
        <Route path="awards" element={<AwardsPage />} />
        <Route path="contracts" element={<ContractsPage />} />
        <Route path="facilities" element={<FacilitiesPage />} />
        <Route path="clauses" element={<ClausesPage />} />
        <Route path="shortlist" element={<ShortlistPage />} />
        <Route path="match-plans" element={<MatchPlansPage />} />
        <Route path="manager" element={<ManagerProfilePage />} />
        <Route path="decisions" element={<DecisionsPage />} />
        <Route path="news" element={<NewsPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="squad" element={<Squad />} />
        <Route path="player/:id" element={<PlayerPage />} />
        <Route path="team/:id" element={<TeamPage />} />
        <Route path="tactics" element={<TacticsPage />} />
        <Route path="training" element={<TrainingPage />} />
        <Route path="medical" element={<MedicalPage />} />
        <Route path="market" element={<MarketPage />} />
        <Route path="market/player/:id" element={<MarketPlayerPage />} />
        <Route path="market/offers" element={<OffersPage />} />
        <Route path="market/renew" element={<RenewPage />} />
        <Route path="commercial" element={<CommercialPage />} />
        <Route path="staff" element={<StaffPage />} />
        <Route path="youth" element={<YouthPage />} />
        <Route path="press" element={<PressPage />} />
        <Route path="press/post" element={<PostPressPage />} />
        <Route path="table" element={<TablePage />} />
        <Route path="promotion" element={<PromotionPage />} />
        <Route path="objectives" element={<ObjectivesPage />} />
        <Route path="cup" element={<CupPage />} />
        <Route path="ehl" element={<EhlPage />} />
        <Route path="match" element={<MatchPreview />} />
        <Route path="live" element={<LiveMatch />} />
        <Route path="report" element={<ReportPage />} />
        <Route path="season-end" element={<SeasonEndPage />} />
        <Route path="options" element={<Options embedded />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
