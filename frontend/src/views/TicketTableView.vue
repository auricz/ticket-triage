<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import FilterBar from '../components/FilterBar.vue'
import { useNow } from '../composables/useNow'
import { useAuthStore } from '../stores/auth'
import { useTicketStore } from '../stores/tickets'
import { formatRemaining, replyDeadline, resolveDeadline, urgencyTimestamp } from '../utils/sla'
import { severityClass } from '../utils/severity'

const TOP_N = 10

const ticketStore = useTicketStore()
const auth = useAuthStore()
const router = useRouter()
const now = useNow()

const teamFilter = ref<number | null>(null)
const severityFilter = ref<number | null>(null)
const search = ref('')

const topTickets = computed(() => {
  const query = search.value.trim().toLowerCase()

  // The API only returns unresolved tickets, but live updates can deliver resolved ones
  return ticketStore.tickets
    .filter((ticket) => ticket.resolved_at === null)
    .filter((ticket) => teamFilter.value === null || ticket.assigned_team_id === teamFilter.value)
    .filter((ticket) => severityFilter.value === null || ticket.sev_id === severityFilter.value)
    .filter((ticket) => {
      if (!query) return true
      const subject = ticket.email_subject?.toLowerCase() ?? ''
      return ticket.requestor_email.toLowerCase().includes(query) || subject.includes(query)
    })
    .map((ticket) => {
      const severity = ticketStore.severityById.get(ticket.sev_id)
      return { ticket, severity, urgency: severity ? urgencyTimestamp(ticket, severity) : Infinity }
    })
    .filter((row) => row.severity !== undefined)
    .sort((a, b) => a.urgency - b.urgency)
    .slice(0, TOP_N)
})

function teamName(id: number): string {
  return ticketStore.departmentById.get(id)?.name ?? 'Unknown'
}

function openTicket(id: number) {
  router.push({ name: 'ticket-detail', params: { id } })
}

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <h1>Ticket Triage</h1>
      <button class="logout" @click="handleLogout">Log out</button>
    </header>

    <FilterBar
      v-model:team="teamFilter"
      v-model:severity="severityFilter"
      v-model:search="search"
      :departments="ticketStore.departments"
      :severities="ticketStore.severities"
    />

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Requester</th>
            <th>Subject</th>
            <th>Team</th>
            <th>Severity</th>
            <th>Time to Reply</th>
            <th>Time to Resolve</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="{ ticket, severity } in topTickets"
            :key="ticket.id"
            class="ticket-row"
            :class="{ flash: ticketStore.recentlyChanged.has(ticket.id) }"
            @click="openTicket(ticket.id)"
          >
            <td>{{ ticket.requestor_email }}</td>
            <td>{{ ticket.email_subject || '(no subject)' }}</td>
            <td>{{ teamName(ticket.assigned_team_id) }}</td>
            <td>
              <span class="badge" :class="severityClass(severity!.name)">{{ severity!.name }}</span>
            </td>
            <td>
              <span v-if="ticket.replied_at" class="done">Replied</span>
              <span v-else :class="{ overdue: replyDeadline(ticket, severity!).getTime() < now }">
                {{ formatRemaining(replyDeadline(ticket, severity!), now) }}
              </span>
            </td>
            <td>
              <span :class="{ overdue: resolveDeadline(ticket, severity!).getTime() < now }">
                {{ formatRemaining(resolveDeadline(ticket, severity!), now) }}
              </span>
            </td>
          </tr>
          <tr v-if="!topTickets.length && ticketStore.loaded">
            <td colspan="6" class="empty">No tickets match these filters.</td>
          </tr>
          <tr v-if="!ticketStore.loaded && ticketStore.loading">
            <td colspan="6" class="empty">Loading tickets…</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.page-header h1 {
  font-size: 1.2rem;
  margin: 0;
}

.logout {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
}

.table-wrap {
  padding: 1.5rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

th,
td {
  text-align: left;
  padding: 0.65rem 1rem;
  border-bottom: 1px solid var(--color-border);
  font-size: 0.9rem;
}

th {
  color: var(--color-text-muted);
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.ticket-row {
  cursor: pointer;
}

.ticket-row:hover {
  background: var(--color-bg);
}

.ticket-row:last-child td {
  border-bottom: none;
}

.badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
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

.overdue {
  color: var(--color-danger);
  font-weight: 600;
}

.done {
  color: var(--color-text-muted);
}

.empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: 2rem;
}

.flash {
  animation: row-fade-in 1.2s ease;
}

@keyframes row-fade-in {
  0% {
    background-color: var(--color-flash);
    opacity: 0.3;
  }
  100% {
    background-color: transparent;
    opacity: 1;
  }
}
</style>
