<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { connectSocket } from './api/socket'
import { useAuthStore } from './stores/auth'
import { useTicketStore } from './stores/tickets'

const auth = useAuthStore()
const ticketStore = useTicketStore()

onMounted(() => {
  if (auth.isAuthenticated && auth.token) {
    connectSocket(auth.token)
    ticketStore.loadAll()
  }
})

watch(
  () => auth.isAuthenticated,
  (isAuthenticated) => {
    if (isAuthenticated) ticketStore.loadAll()
  },
)
</script>

<template>
  <router-view />
</template>
