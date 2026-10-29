import { useEffect, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { AlertTriangle, CheckCircle2, Inbox, Loader2, X } from 'lucide-react'

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/game" className="brand">
      <span className="brand-mark">H</span>
      {!compact && (
        <span className="brand-copy">
          <b>HOCKEY</b>
          <small>MANAGER</small>
        </span>
      )}
    </Link>
  )
}

export function Crest({
  src,
  name,
  size = 44,
  className = '',
}: {
  src?: string
  name: string
  size?: number
  className?: string
}) {
  const [broken, setBroken] = useState(false)
  const letters = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
  if (!src || broken) {
    return (
      <span className={`crest crest-fallback ${className}`} style={{ width: size, height: size, fontSize: size * 0.3 }} aria-hidden="true">
        {letters || '?'}
      </span>
    )
  }
  return <img className={`crest ${className}`} src={src} alt={`Escudo ${name}`} style={{ width: size, height: size }} onError={() => setBroken(true)} />
}

export function Avatar({ player, size = 44, className = '' }: { player: { name: string; photo?: string; initials?: string }; size?: number; className?: string }) {
  const [broken, setBroken] = useState(false)
  const fallback = player.initials || player.name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
  if (!player.photo || broken) {
    return (
      <span className={`avatar avatar-fallback ${className}`} style={{ width: size, height: size, fontSize: size * 0.28 }} aria-hidden="true">
        {fallback}
      </span>
    )
  }
  return <img className={`avatar ${className}`} src={player.photo} alt={player.name} style={{ width: size, height: size }} onError={() => setBroken(true)} />
}

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'blue'
type ButtonSize = 'sm' | 'md' | 'lg'

export function Button({
  children,
  variant = 'secondary',
  size = 'md',
  loading = false,
  icon: Icon,
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  icon?: LucideIcon
}) {
  return (
    <button className={`btn btn-${variant} btn-${size} ${className}`} {...props} disabled={props.disabled || loading}>
      {loading ? <Loader2 size={16} className="spin" /> : Icon ? <Icon size={16} /> : null}
      <span>{children}</span>
    </button>
  )
}

export function Badge({ children, tone = 'neutral', className = '' }: { children: ReactNode; tone?: 'neutral' | 'ok' | 'warn' | 'danger' | 'gold' | 'blue'; className?: string }) {
  return <span className={`badge badge-${tone} ${className}`}>{children}</span>
}

export function Card({ children, className = '', padded = true }: { children: ReactNode; className?: string; padded?: boolean }) {
  return <section className={`card ${padded ? 'card-padded' : ''} ${className}`}>{children}</section>
}

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  actions,
  className = '',
}: {
  eyebrow?: string
  title: string
  subtitle?: ReactNode
  actions?: ReactNode
  className?: string
}) {
  return (
    <header className={`page-header ${className}`}>
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  )
}

export function StatCard({
  label,
  value,
  hint,
  tone = 'default',
  icon: Icon,
}: {
  label: string
  value: ReactNode
  hint?: ReactNode
  tone?: 'default' | 'gold' | 'blue' | 'ok' | 'danger'
  icon?: LucideIcon
}) {
  return (
    <div className={`stat-card stat-${tone}`}>
      <div className="stat-top">
        <span>{label}</span>
        {Icon && <Icon size={15} />}
      </div>
      <strong>{value}</strong>
      {hint && <small>{hint}</small>}
    </div>
  )
}

export function Progress({ value, tone = 'gold', className = '' }: { value: number; tone?: 'gold' | 'ok' | 'blue' | 'danger'; className?: string }) {
  return (
    <div className={`progress ${className}`}>
      <span className={`progress-${tone}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  )
}

export function SectionTitle({ title, aside }: { title: string; aside?: ReactNode }) {
  return (
    <div className="section-title">
      <h2>{title}</h2>
      {aside}
    </div>
  )
}

export function EmptyState({ title, body, action }: { title: string; body?: string; action?: ReactNode }) {
  return (
    <div className="empty-state">
      <Inbox size={28} />
      <h3>{title}</h3>
      {body && <p>{body}</p>}
      {action}
    </div>
  )
}

export function LoadingBlock({ label = 'Cargando…' }: { label?: string }) {
  return (
    <div className="loading-block">
      <Loader2 className="spin" size={20} />
      <span>{label}</span>
    </div>
  )
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  )
}

export function Modal({
  open,
  title,
  children,
  onClose,
  wide = false,
}: {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
  wide?: boolean
}) {
  const modalRef = useRef<HTMLDivElement>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    if (!open) return
    const previous = document.activeElement as HTMLElement | null
    const node = modalRef.current
    const focusable = () =>
      Array.from(
        node?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ) || [],
      )
    const first = focusable()[0]
    first?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onCloseRef.current()
        return
      }
      if (event.key !== 'Tab') return
      const items = focusable()
      if (!items.length) return
      const firstItem = items[0]
      const lastItem = items[items.length - 1]
      if (event.shiftKey && document.activeElement === firstItem) {
        event.preventDefault()
        lastItem.focus()
      } else if (!event.shiftKey && document.activeElement === lastItem) {
        event.preventDefault()
        firstItem.focus()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      previous?.focus()
    }
  }, [open])

  if (!open) return null
  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div ref={modalRef} className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Cerrar">
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}

export function Notice({ tone = 'info', children }: { tone?: 'info' | 'ok' | 'warn' | 'danger'; children: ReactNode }) {
  const Icon = tone === 'ok' ? CheckCircle2 : tone === 'danger' || tone === 'warn' ? AlertTriangle : Inbox
  return (
    <div className={`notice notice-${tone}`}>
      <Icon size={16} />
      <div>{children}</div>
    </div>
  )
}

export function Tabs<T extends string>({
  tabs,
  value,
  onChange,
}: {
  tabs: Array<{ value: T; label: string; count?: number }>
  value: T
  onChange: (value: T) => void
}) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          role="tab"
          aria-selected={tab.value === value}
          className={`tab ${tab.value === value ? 'active' : ''}`}
          onClick={() => onChange(tab.value)}
        >
          {tab.label}
          {tab.count !== undefined && <span>{tab.count}</span>}
        </button>
      ))}
    </div>
  )
}
