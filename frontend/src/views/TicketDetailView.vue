<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, ApiError } from '../api/client'
import { useTicketStore } from '../stores/tickets'
import type { AuditLogEntry } from '../types'
import { severityClass } from '../utils/severity'

const props = defineProps<{ id: string }>()

const ticketStore = useTicketStore()
const router = useRouter()

const ticketId = computed(() => Number(props.id))
const ticket = computed(() => ticketStore.ticketsById.get(ticketId.value))

const auditLog = ref<AuditLogEntry[]>([])
const auditError = ref<string | null>(null)
const actionError = ref<string | null>(null)
const busy = ref(false)

const sortedAuditLog = computed(() => [...auditLog.value].reverse())

async function loadAuditLog() {
  auditError.value = null
  try {
    auditLog.value = await api.getAuditLog(ticketId.value)
  } catch (err) {
    auditError.value = err instanceof ApiError ? err.message : 'Failed to load audit log'
  }
}

onMounted(loadAuditLog)
watch(ticketId, loadAuditLog)

async function markReplied() {
  if (!ticket.value || ticket.value.replied_at || busy.value) return
  actionError.value = null
  busy.value = true
  try {
    const updated = await api.markReplied(ticket.value.id)
    ticketStore.upsertTicket(updated)
    await loadAuditLog()
  } catch (err) {
    actionError.value = err instanceof ApiError ? err.message : 'Failed to mark as replied'
  } finally {
    busy.value = false
  }
}

async function markResolved() {
  if (!ticket.value || ticket.value.resolved_at || busy.value) return
  actionError.value = null
  busy.value = true
  try {
    const updated = await api.markResolved(ticket.value.id)
    ticketStore.upsertTicket(updated)
    await loadAuditLog()
  } catch (err) {
    actionError.value = err instanceof ApiError ? err.message : 'Failed to mark as resolved'
  } finally {
    busy.value = false
  }
}

async function changeTeam(event: Event) {
  if (!ticket.value) return
  const assignedTeamId = Number((event.target as HTMLSelectElement).value)
  actionError.value = null
  try {
    const updated = await api.updateTeam(ticket.value.id, assignedTeamId)
    ticketStore.upsertTicket(updated)
    await loadAuditLog()
  } catch (err) {
    actionError.value = err instanceof ApiError ? err.message : 'Failed to change team'
  }
}

async function changeSeverity(event: Event) {
  if (!ticket.value) return
  const sevId = Number((event.target as HTMLSelectElement).value)
  actionError.value = null
  try {
    const updated = await api.updateSeverity(ticket.value.id, sevId)
    ticketStore.upsertTicket(updated)
    await loadAuditLog()
  } catch (err) {
    actionError.value = err instanceof ApiError ? err.message : 'Failed to change severity'
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <button class="back" @click="router.push({ name: 'tickets' })">&larr; Back to tickets</button>
    </header>

    <div v-if="!ticket && ticketStore.loading" class="not-found">Loading ticket…</div>
    <div v-else-if="!ticket" class="not-found">Ticket not found.</div>

    <div v-else class="content">
      <section class="panel">
        <h1>{{ ticket.email_subject || '(no subject)' }}</h1>
        <p class="requestor">From {{ ticket.requestor_email }} &middot; {{ formatDate(ticket.created_at) }}</p>

        <div class="fields">
          <label>
            Team
            <select :value="ticket.assigned_team_id" @change="changeTeam">
              <option v-for="dept in ticketStore.departments" :key="dept.id" :value="dept.id">
                {{ dept.name }}
              </option>
            </select>
          </label>

          <label>
            Severity
            <select :value="ticket.sev_id" @change="changeSeverity">
              <option v-for="sev in ticketStore.severities" :key="sev.id" :value="sev.id">
                {{ sev.name }}
              </option>
            </select>
          </label>

          <span v-if="ticketStore.severityById.get(ticket.sev_id)" class="badge" :class="severityClass(ticketStore.severityById.get(ticket.sev_id)!.name)">
            {{ ticketStore.severityById.get(ticket.sev_id)!.name }}
          </span>
        </div>

        <p v-if="actionError" class="error">{{ actionError }}</p>

        <div class="actions">
          <button :disabled="!!ticket.replied_at || busy" @click="markReplied">
            {{ ticket.replied_at ? 'Replied' : 'Mark as Replied' }}
          </button>
          <button :disabled="!!ticket.resolved_at || busy" @click="markResolved">
            {{ ticket.resolved_at ? 'Resolved' : 'Mark as Resolved' }}
          </button>
        </div>
      </section>

      <section class="panel">
        <h2>Original Message</h2>
        <p class="message-body">{{ ticket.email_body || '(no message body)' }}</p>
      </section>

      <section class="panel">
        <h2>AI Explanation</h2>
        <p class="message-body">{{ ticket.ai_explaination || 'No explanation provided.' }}</p>
      </section>

      <section class="panel">
        <h2>Audit Log</h2>
        <p v-if="auditError" class="error">{{ auditError }}</p>
        <ul v-else class="audit-log">
          <li v-for="entry in sortedAuditLog" :key="entry.id">
            <span class="audit-action">{{ entry.action }}</span>
            <span class="audit-meta">{{ entry.username }} &middot; {{ formatDate(entry.created_at) }}</span>
          </li>
          <li v-if="!sortedAuditLog.length" class="empty">No history yet.</li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
}

.page-header {
  padding: 1rem 1.5rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.back {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: 0.9rem;
  padding: 0;
}

.not-found {
  padding: 3rem;
  text-align: center;
  color: var(--color-text-muted);
}

.content {
  max-width: 720px;
  margin: 0 auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
}

.panel h1 {
  margin: 0 0 0.3rem;
  font-size: 1.3rem;
}

.panel h2 {
  margin: 0 0 0.75rem;
  font-size: 1rem;
}

.requestor {
  margin: 0 0 1rem;
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.fields {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.fields label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

select {
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.badge {
  align-self: flex-end;
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  color: white;
}

.sev-high {
  background: var(--color-sev-high);
}

.sev-med {
  background: var(--color-sev-med);
}

.sev-low {
  background: var(--color-sev-low);
}

.actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

.actions button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-primary);
  background: var(--color-primary);
  color: white;
  border-radius: 6px;
  font-size: 0.9rem;
}

.actions button:disabled {
  background: var(--color-border);
  border-color: var(--color-border);
  color: var(--color-text-muted);
}

.message-body {
  white-space: pre-wrap;
  color: var(--color-text);
  line-height: 1.5;
  margin: 0;
}

.error {
  color: var(--color-danger);
  font-size: 0.85rem;
}

.audit-log {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.audit-log li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.6rem;
  font-size: 0.88rem;
}

.audit-log li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.audit-action {
  text-transform: capitalize;
}

.audit-meta {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  white-space: nowrap;
}

.empty {
  color: var(--color-text-muted);
  justify-content: center;
}
</style>
