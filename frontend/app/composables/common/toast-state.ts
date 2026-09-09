import type { Ref } from 'vue'

export type ToastItem = {
  id: string
  open: boolean
  title?: string
  description?: string
  color?: string
}

/**
 * Shared toast state: written by `useApi()` / `useAccessAlert()` error paths
 * and rendered by Nuxt UI's `<UApp>` Toaster (Nuxt UI's `useToast()` reads the
 * same `'toasts'` state key).
 *
 * Call this ONLY while a Nuxt context is alive (setup, plugin, middleware,
 * store creation) and reuse the returned ref from delayed callbacks. Calling
 * `useState()` again from a delayed callback (ofetch response hooks, timers)
 * runs without the Nuxt instance and throws NUXT_E1001.
 */
export function useAppToastState(): Ref<ToastItem[]> {
  return useState<ToastItem[]>('toasts', () => [])
}

/** Append a toast to the shared state, keeping the newest five. */
export function appendAppToast(toasts: Ref<ToastItem[]>, toast: Omit<ToastItem, 'id' | 'open'>) {
  const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  toasts.value = [...toasts.value, { id, open: true, ...toast }].slice(-5)
}
