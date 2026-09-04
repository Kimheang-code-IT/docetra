type ToastItem = {
  id: string
  open: boolean
  title?: string
  description?: string
  color?: string
}

function pushToast(title: string, description: string, color: ToastItem['color'] = 'error') {
  const toasts = useState<ToastItem[]>('toasts', () => [])
  const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  toasts.value = [...toasts.value, { id, open: true, title, description, color }].slice(-5)
}

/**
 * Permission / session feedback without a blocking modal.
 * 401 still clears the session in `useApi`; this only toasts.
 */
export function useAccessAlert() {
  const nuxtApp = useNuxtApp()

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
