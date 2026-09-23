import type { Severity, Ticket } from '../types'

export function replyDeadline(ticket: Ticket, severity: Severity): Date {
  return new Date(new Date(ticket.created_at).getTime() + severity.respond_time_hours * 3_600_000)
}

export function resolveDeadline(ticket: Ticket, severity: Severity): Date {
  return new Date(new Date(ticket.created_at).getTime() + severity.resolve_time_hours * 3_600_000)
}

export function isFullyDone(ticket: Ticket): boolean {
  return ticket.replied_at !== null && ticket.resolved_at !== null
}

// Soonest deadline among the SLA clocks still pending for this ticket.
// Used to rank tickets by urgency (least time left first).
export function urgencyTimestamp(ticket: Ticket, severity: Severity): number {
  const pending: number[] = []
  if (!ticket.replied_at) pending.push(replyDeadline(ticket, severity).getTime())
  if (!ticket.resolved_at) pending.push(resolveDeadline(ticket, severity).getTime())
  return pending.length ? Math.min(...pending) : Infinity
}

export function formatRemaining(deadline: Date, now: number): string {
  const diffMs = deadline.getTime() - now
  const overdue = diffMs < 0
  const totalMinutes = Math.floor(Math.abs(diffMs) / 60_000)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  const text = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`
  return overdue ? `Overdue by ${text}` : text
}
