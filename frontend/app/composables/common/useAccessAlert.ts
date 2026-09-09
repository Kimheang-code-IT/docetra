import { appendAppToast, useAppToastState, type ToastItem } from '~/composables/common/toast-state'

/**
 * Permission / session feedback without a blocking modal.
 * 401 still clears the session in `useApi`; this only toasts.
 */
export function useAccessAlert() {
  const nuxtApp = useNuxtApp()
  // Captured while the Nuxt instance is current. Delayed callbacks (ofetch
  // response hooks) must reuse this ref — a fresh useState() call from a
  // delayed hook throws NUXT_E1001.
  const toasts = useAppToastState()

  function pushToast(title: string, description: string, color: ToastItem['color'] = 'error') {
    appendAppToast(toasts, { title, description, color })
  }

  function t(key: string, params?: Record<string, unknown>) {
    const i18n = nuxtApp.$i18n as { t: (k: string, p?: Record<string, unknown>) => string } | undefined
    return i18n?.t?.(key, params) ?? key
  }

  function showPermissionDenied(options: {
    permission?: string
    requestedPath?: string
    description?: string
  } = {}) {
    pushToast(
      t('docetra.states.accessDeniedTitle'),
      options.description || t('docetra.states.accessDeniedDescription'),
    )
  }

  function showSessionExpired(description = '') {
    pushToast(
      t('docetra.states.sessionExpiredTitle'),
      description || t('docetra.states.sessionExpiredDescription'),
      'warning',
    )
  }

  return {
    showPermissionDenied,
    showSessionExpired,
  }
}
