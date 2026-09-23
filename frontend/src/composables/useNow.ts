import { onMounted, onUnmounted, ref } from 'vue'

// A shared reactive clock so countdown cells re-render without per-row timers.
export function useNow(intervalMs = 30_000) {
  const now = ref(Date.now())
  let handle: number | undefined

  onMounted(() => {
    handle = window.setInterval(() => {
      now.value = Date.now()
    }, intervalMs)
  })

  onUnmounted(() => {
    if (handle !== undefined) window.clearInterval(handle)
  })

  return now
}
