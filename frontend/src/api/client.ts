import { useAuthStore } from '../stores/auth'
import type { AuditLogEntry, Department, Severity, Ticket, TicketListResponse } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const auth = useAuthStore()
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (auth.token) headers.set('Authorization', `Bearer ${auth.token}`)

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (response.status === 403) {
    auth.logout()
    throw new ApiError(403, 'Session expired, please log in again')
  }

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, body?.error ?? body?.message ?? 'Request failed')
  }
  return body as T
}

export const api = {
  login: (username: string, password: string) =>
    request<{ token: string }>('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  getDepartments: () => request<Department[]>('/departments'),

  getSeverities: () => request<Severity[]>('/severities'),

  getTickets: (page: number, perPage: number) =>
    request<TicketListResponse>(`/tickets?page=${page}&per_page=${perPage}`),

  updateTeam: (id: number, assignedTeamId: number) =>
    request<Ticket>(`/tickets/${id}/team`, {
      method: 'PATCH',
      body: JSON.stringify({ assigned_team_id: assignedTeamId }),
    }),

  updateSeverity: (id: number, sevId: number) =>
    request<Ticket>(`/tickets/${id}/severity`, {
      method: 'PATCH',
      body: JSON.stringify({ sev_id: sevId }),
    }),

  markReplied: (id: number) => request<Ticket>(`/tickets/${id}/reply`, { method: 'PATCH' }),

  markResolved: (id: number) => request<Ticket>(`/tickets/${id}/resolve`, { method: 'PATCH' }),

  getAuditLog: (id: number) => request<AuditLogEntry[]>(`/tickets/${id}/audit`),
}
