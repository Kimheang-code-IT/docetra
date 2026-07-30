import { ensureMinReloadDuration } from '~/utils/reload-min-duration'

export function useMockTableReload(reload: () => void) {
  const isReloading = ref(false)
  let reloadPromise: Promise<void> | null = null

  async function retryFetch() {
    if (reloadPromise) return reloadPromise

    isReloading.value = true
    const startedAt = Date.now()
    reloadPromise = (async () => {
      try {
        reload()
        await nextTick()
      } finally {
        await ensureMinReloadDuration(startedAt)
        isReloading.value = false
        reloadPromise = null
      }
    })()

    return reloadPromise
  }

  return { isReloading, retryFetch }
}
