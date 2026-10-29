import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BriefcaseBusiness, MessageSquare, Plus, ShieldCheck, UserMinus } from 'lucide-react'
import { api } from '../lib/api'
import { money } from '../lib/format'
import type { Candidate, StaffCandidatesPayload, StaffPayload } from '../types'
import { useGame } from '../context/GameContext'
import { useToast } from '../context/ToastContext'
import { Avatar, Badge, Button, Card, LoadingBlock, Modal, PageHeader, Progress } from '../components/ui'

export default function StaffPage() {
  const navigate = useNavigate()
  const { applyState } = useGame()
  const { toast } = useToast()
  const [data, setData] = useState<StaffPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [role, setRole] = useState<string | null>(null)
  const [candidates, setCandidates] = useState<StaffCandidatesPayload | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  function load() {
    setLoading(true)
    api.get<StaffPayload>('/staff')
      .then(({ data }) => setData(data))
      .catch((err) => toast(err instanceof Error ? err.message : 'No se pudo cargar el staff.', 'danger'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function openCandidates(nextRole: string) {
    setRole(nextRole)
    setCandidates(null)
    try {
      const { data } = await api.get<StaffCandidatesPayload>(`/staff/${nextRole}/candidates`)
      setCandidates(data)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudieron cargar los candidatos.', 'danger')
    }
  }

  async function hire(candidate: Candidate, index: number) {
    if (!role) return
    setBusy(`hire-${index}`)
    try {
      const response = await api.post<{ state: unknown }>(`/staff/hire/${role}`, { candidate: index })
      applyState(response.data.state as never)
      toast(response.message || 'Staff contratado.', 'success')
      setRole(null)
      setCandidates(null)
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo contratar.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  async function fire(memberRole: string) {
    setBusy(`fire-${memberRole}`)
    try {
      const response = await api.post<{ state: unknown }>(`/staff/fire/${memberRole}`)
      applyState(response.data.state as never)
      toast(response.message || 'Staff despedido.', 'info')
      load()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'No se pudo despedir.', 'danger')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingBlock label="Cargando cuerpo técnico…" />
  if (!data) return <Card><p className="muted">No se pudo cargar el staff.</p></Card>
  const team = data.team
  const technical = team.staff.filter((member) => member.role !== 'head_coach')

  return (
    <>
      <PageHeader
        eyebrow={`${team.name} · ${team.city}`}
        title="Staff y junta"
        subtitle={`Cuerpo técnico, banquillo y confianza institucional. Academia ${team.academy_rating}/100.`}
        actions={<Badge tone={team.board_confidence >= 60 ? 'ok' : 'warn'}>Confianza {team.board_confidence}/100</Badge>}
      />

      <div className="split-2">
        <Card>
          <div className="inline" style={{ justifyContent: 'space-between' }}><h3 style={{ margin: 0 }}>Staff técnico</h3><Badge tone="neutral">{technical.length} perfiles</Badge></div>
          <div className="stack-sm mt-2">
            <div className="squad-status-row">
              <span className="board-icon">T</span>
              <span className="squad-status-main"><b>Tú</b><span>Entrenador · manager del club</span></span>
              <Badge tone="gold">Manager</Badge>
            </div>
            {technical.map((member) => (
              <div className="squad-status-row" key={member.role}>
                <Avatar player={{ name: member.name, initials: member.name.slice(0, 2) }} size={34} />
                <span className="squad-status-main"><b>{member.name}</b><span>{member.role_label} · {member.rating}/100 · relación {member.relationship}/100 · moral {member.morale}/20</span></span>
                <Button size="sm" variant="ghost" icon={MessageSquare} onClick={() => navigate(`/game/chat?target_type=staff&target_id=${encodeURIComponent(member.role)}`)}>Hablar</Button>
                <Button size="sm" variant="danger" icon={UserMinus} onClick={() => fire(member.role)} loading={busy === `fire-${member.role}`}>Despedir</Button>
              </div>
            ))}
            {!technical.length && <p className="small muted">Todavía no hay cuerpo técnico contratado.</p>}
          </div>
          <h3 className="mt-2">Contratar</h3>
          <div className="actions">
            {data.free_roles.map((freeRole) => (
              <Button key={freeRole} size="sm" icon={Plus} onClick={() => openCandidates(freeRole)}>{data.staff_labels[freeRole]}</Button>
            ))}
            {!data.free_roles.length && <p className="small muted">Todos los roles están cubiertos.</p>}
          </div>
        </Card>
        <Card>
          <h3>Junta directiva</h3>
          <div className="stack-sm">
            {team.board.map((member) => (
              <div className="squad-status-row" key={member.role}>
                <span className="board-icon">{member.role.slice(0, 1).toUpperCase()}</span>
                <span className="squad-status-main"><b>{member.name}</b><span>{member.role.replaceAll('_', ' ')} · {member.source}</span></span>
                <Badge tone="neutral">{member.confidence}</Badge>
              </div>
            ))}
          </div>
          <div className="stack-sm mt-2">
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Confianza</span><b className="small">{team.board_confidence}/100</b></div><Progress value={team.board_confidence} tone="ok" /></div>
            <div><div className="inline" style={{ justifyContent: 'space-between' }}><span className="small muted">Presión</span><b className="small">{team.board_pressure}</b></div><Progress value={team.board_patience * 20} tone="gold" /></div>
            <p className="small muted">Objetivo: {team.board_expectation}</p>
          </div>
        </Card>
      </div>

      <Card className="mt-2">
        <h3>Efectos del staff</h3>
        <div className="attr-grid">
          {[['Segundo entrenador', 'assistant'], ['Preparador físico', 'fitness_coach'], ['Fisioterapeuta', 'physio'], ['Analista', 'performance_analyst'], ['Entrenador de porteros', 'gk_coach'], ['Ojeador', 'scout']].map(([label, staffRole]) => {
            const rating = team.staff.find((member) => member.role === staffRole)?.rating || 55
            return <div key={staffRole}><div className="attr-row"><span>{label}</span><div className="attr-bar"><span style={{ width: `${rating}%` }} /></div><b>{rating}</b></div></div>
          })}
        </div>
      </Card>

      <Modal open={Boolean(role)} title={`Candidatos · ${role ? data.staff_labels[role] : ''}`} onClose={() => setRole(null)} wide>
        {!candidates ? <LoadingBlock label="Buscando candidatos…" /> : (
          <div className="stack-sm">
            {candidates.candidates.map((candidate, index) => (
              <div className="squad-status-row" key={`${candidate.name}-${index}`}>
                <Avatar player={{ name: candidate.name, initials: candidate.name.slice(0, 2) }} size={38} />
                <span className="squad-status-main"><b>{candidate.name}</b><span>{candidate.rating}/100 · {money(candidate.salary)} · {candidate.source}</span></span>
                <Button size="sm" variant="primary" icon={BriefcaseBusiness} onClick={() => hire(candidate, index)} loading={busy === `hire-${index}`}>Contratar</Button>
              </div>
            ))}
            {!candidates.candidates.length && <p className="small muted">No hay candidatos disponibles.</p>}
          </div>
        )}
      </Modal>
    </>
  )
}
