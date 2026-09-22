<script setup lang="ts">
import type { Department, Severity } from '../types'

defineProps<{
  departments: Department[]
  severities: Severity[]
}>()

const team = defineModel<number | null>('team', { required: true })
const severity = defineModel<number | null>('severity', { required: true })
const search = defineModel<string>('search', { required: true })
</script>

<template>
  <div class="filter-bar">
    <select v-model="team">
      <option :value="null">All teams</option>
      <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
    </select>

    <select v-model="severity">
      <option :value="null">All severities</option>
      <option v-for="sev in severities" :key="sev.id" :value="sev.id">{{ sev.name }}</option>
    </select>

    <input v-model="search" type="search" placeholder="Search requestor or subject…" />
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

select,
input {
  padding: 0.45rem 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

input[type='search'] {
  flex: 1;
  min-width: 200px;
}
</style>
