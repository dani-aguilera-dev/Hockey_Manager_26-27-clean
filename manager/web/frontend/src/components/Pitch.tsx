import type { SlotRow } from '../types'
import { Avatar } from './ui'

export function Pitch({
  rows,
  formation,
  selectable = false,
  activeSlot,
  onSlotClick,
}: {
  rows: SlotRow[]
  formation?: string
  selectable?: boolean
  activeSlot?: number | null
  onSlotClick?: (index: number) => void
}) {
  const ordered = [...rows].reverse()
  return (
    <div className="pitch">
      <div className="pitch-lines" aria-hidden="true">
        <span className="pitch-halfway" />
        <span className="pitch-circle" />
        <span className="pitch-box pitch-box-top" />
        <span className="pitch-box pitch-box-bottom" />
      </div>
      {formation && <div className="pitch-formation">{formation}</div>}
      <div className="pitch-rows">
        {ordered.map((row) => (
          <div className="pitch-row" key={row.label}>
            <span className="pitch-row-label">{row.label}</span>
            <div className="pitch-slots">
              {row.slots.map((slot) => {
                const player = slot.player
                return (
                  <div
                    className={`slot ${slot.mismatch ? 'slot-mismatch' : ''} ${selectable ? 'slot-clickable' : ''} ${activeSlot === slot.index ? 'slot-active' : ''}`}
                    key={slot.index}
                    role={selectable ? 'button' : undefined}
                    tabIndex={selectable ? 0 : undefined}
                    onClick={selectable ? () => onSlotClick?.(slot.index) : undefined}
                    onKeyDown={selectable ? (event) => { if (event.key === 'Enter' || event.key === ' ') onSlotClick?.(slot.index) } : undefined}
                    aria-label={selectable ? `Cambiar ${slot.code}` : undefined}
                  >
                    <div className="slot-top">
                      <span className="slot-code">{slot.code}</span>
                      {player && <span className="slot-ovr">{player.overall.toFixed(1)}</span>}
                    </div>
                    {player ? (
                      <>
                        <Avatar player={player} size={40} />
                        <b className="slot-name">{player.name.split(' ').slice(0, 2).join(' ')}</b>
                        <small>{player.subposition}</small>
                        {slot.mismatch && <span className="slot-warning">Fuera de posición</span>}
                      </>
                    ) : (
                      <span className="slot-empty">Elegir jugador</span>
                    )}
                    {selectable && <span className="slot-change">Cambiar</span>}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
