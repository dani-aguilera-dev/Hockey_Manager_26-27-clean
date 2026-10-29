export function money(value: number | null | undefined): string {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value || 0)
}

export function compactMoney(value: number | null | undefined): string {
  const n = value || 0
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace('.', ',')} M €`
  if (Math.abs(n) >= 1_000) return `${Math.round(n / 1_000)} K €`
  return `${n} €`
}

export function number(value: number | null | undefined, digits = 0): string {
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value || 0)
}

export function dateLabel(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    const date = new Date(`${iso.slice(0, 10)}T12:00:00`)
    return new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'short', year: 'numeric' }).format(date)
  } catch {
    return iso
  }
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    const date = new Date(`${iso.slice(0, 10)}T12:00:00`)
    return new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'short' }).format(date)
  } catch {
    return iso
  }
}

export function dayMonth(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    const date = new Date(`${iso.slice(0, 10)}T12:00:00`)
    return new Intl.DateTimeFormat('es-ES', { weekday: 'short', day: '2-digit', month: 'short' }).format(date)
  } catch {
    return iso
  }
}

export function titleCase(value: string | null | undefined): string {
  return String(value || '')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function initials(name: string): string {
  return String(name || '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

export function positionLabel(position: number | null | undefined): string {
  if (!position) return '—'
  return `${position}º`
}

export function resultTone(result: string): 'ok' | 'warn' | 'danger' {
  if (result === 'Victoria') return 'ok'
  if (result === 'Empate') return 'warn'
  return 'danger'
}

export function safePercent(value: number | null | undefined): number {
  return clamp(Math.round(value || 0), 0, 100)
}

export function shortLeague(code: string | null | undefined): string {
  const map: Record<string, string> = {
    DHA: 'DHA',
    DHB: 'DHB',
    NED: 'Hoofdklasse',
    BEL: 'Belgian League',
    GER: 'Bundesliga',
    ENG: 'Premier Division',
    ARG: 'Metropolitano',
    IND: 'HIL',
  }
  return map[code || ''] || code || '—'
}
