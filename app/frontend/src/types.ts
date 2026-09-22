export interface Department {
  id: number
  name: string
}

export interface Severity {
  id: number
  name: string
  respond_time_hours: number
  resolve_time_hours: number
}

export interface Ticket {
  id: number
  requestor_email: string
  email_subject: string | null
  email_body: string | null
  assigned_team_id: number
  sev_id: number
  ai_explaination: string | null
  created_at: string
  replied_at: string | null
  resolved_at: string | null
}

export interface AuditLogEntry {
  id: number
  action: string
  created_at: string
  username: string
}

export interface TicketListResponse {
  tickets: Ticket[]
  page: number
  per_page: number
  total: number
  total_pages: number
}
