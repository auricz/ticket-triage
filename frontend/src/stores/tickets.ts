import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '../api/client'
import { registerTicketHandlers } from '../api/socket'
import type { Department, Severity, Ticket } from '../types'

// How long a row keeps its "just changed" fade-in animation.
const FLASH_DURATION_MS = 1200

export const useTicketStore = defineStore('tickets', () => {
  const ticketsById = ref(new Map<number, Ticket>())
  const departments = ref<Department[]>([])
  const severities = ref<Severity[]>([])
  const recentlyChanged = ref(new Map<number, number>())
  const loaded = ref(false)
  const loading = ref(false)

  const tickets = computed(() => Array.from(ticketsById.value.values()))
  const departmentById = computed(() => new Map(departments.value.map((d) => [d.id, d])))
  const severityById = computed(() => new Map(severities.value.map((s) => [s.id, s])))

  function flashTicket(id: number) {
    recentlyChanged.value.set(id, Date.now())
    recentlyChanged.value = new Map(recentlyChanged.value)
    setTimeout(() => {
      recentlyChanged.value.delete(id)
      recentlyChanged.value = new Map(recentlyChanged.value)
    }, FLASH_DURATION_MS)
  }

  function upsertTicket(ticket: Ticket, flash = true) {
    ticketsById.value.set(ticket.id, ticket)
    ticketsById.value = new Map(ticketsById.value)
    if (flash) flashTicket(ticket.id)
  }

  async function loadAll() {
    if (loading.value) return
    loading.value = true
    try {
      const [depts, sevs] = await Promise.all([api.getDepartments(), api.getSeverities()])
      departments.value = depts
      severities.value = sevs

      const all: Ticket[] = []
      let page = 1
      let totalPages = 1
      do {
        const response = await api.getTickets(page, 100)
        all.push(...response.tickets)
        totalPages = response.total_pages
        page += 1
      } while (page <= totalPages)

      ticketsById.value = new Map(all.map((t) => [t.id, t]))
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  registerTicketHandlers({
    onCreated: (ticket) => upsertTicket(ticket),
    onUpdated: (ticket) => upsertTicket(ticket),
  })

  return {
    tickets,
    ticketsById,
    departments,
    severities,
    departmentById,
    severityById,
    recentlyChanged,
    loaded,
    loading,
    loadAll,
    upsertTicket,
  }
})
