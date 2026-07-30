export type AppHeaderBreadcrumb = {
  label: string
  to?: string
  icon?: string
}

export type AppHeaderBadge = {
  label: string
  color?: 'error' | 'neutral' | 'primary' | 'secondary' | 'success' | 'info' | 'warning'
}

/**
 * Shared dynamic header state for layout AppHeader + AppHeaderActions.
 * Left: title or breadcrumbs + badges. Right: teleported actions.
 */
export function useAppHeader() {
  const title = useState('app-header-title', () => '')
  const breadcrumbs = useState<AppHeaderBreadcrumb[]>('app-header-breadcrumbs', () => [])
  const badges = useState<AppHeaderBadge[]>('app-header-badges', () => [])
  const route = useRoute()
  const { t, te } = useI18n()

  const metaTitle = computed(() => {
    const key = route.meta.titleKey
    if (typeof key !== 'string' || !key) return ''
    return te(key) ? t(key) : key
  })

  const displayTitle = computed(() => title.value || metaTitle.value)
  const hasBreadcrumbs = computed(() => breadcrumbs.value.length > 0)

  function setTitle(value: string) {
    title.value = value
    breadcrumbs.value = []
  }

  function setBreadcrumbs(items: AppHeaderBreadcrumb[]) {
    breadcrumbs.value = items
    const last = items[items.length - 1]
    if (last?.label) title.value = last.label
  }

  function setBadges(items: AppHeaderBadge[]) {
    badges.value = items
  }

  function clear() {
    title.value = ''
    breadcrumbs.value = []
    badges.value = []
  }

  /** @deprecated use clear() */
  function clearTitle() {
    clear()
  }

  return {
    title,
    breadcrumbs,
    badges,
    displayTitle,
    hasBreadcrumbs,
    setTitle,
    setBreadcrumbs,
    setBadges,
    clear,
    clearTitle,
  }
}
