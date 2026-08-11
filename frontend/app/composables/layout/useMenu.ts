import type { NavigationMenuItem } from '@nuxt/ui'

const SIDEBAR_COLLAPSED_KEY = 'docetra:sidebar:collapsed'
const SIDEBAR_AUTO_MQ = '(max-width: 1023px)'

/** Shared sidebar state and the single source of truth for Docetra navigation. */
export function useMenu() {
  const open = useState('sidebar-open', () => false)
  const collapsed = useState('sidebar-collapsed', () => false)
  const manualCollapsed = useState<boolean | null>('sidebar-collapsed-manual', () => null)
  const { t } = useI18n()
  const auth = useAuthStore()

  const isNarrow = useMediaQuery(SIDEBAR_AUTO_MQ)
  const hydrated = useState('sidebar-collapsed-hydrated', () => false)

  function close() {
    open.value = false
  }

  function applyAutoCollapse(narrow: boolean) {
    // Respect an explicit user choice for this session; otherwise follow viewport.
    if (manualCollapsed.value != null) {
      collapsed.value = manualCollapsed.value
      return
    }
    collapsed.value = narrow
  }

  function setCollapsed(value: boolean) {
    collapsed.value = value
    manualCollapsed.value = value
    if (import.meta.client) {
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, value ? '1' : '0')
    }
  }

  if (import.meta.client && !hydrated.value) {
    hydrated.value = true
    const saved = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
    if (saved === '1' || saved === '0') {
      manualCollapsed.value = saved === '1'
      collapsed.value = manualCollapsed.value
    }
    else {
      applyAutoCollapse(isNarrow.value)
    }
    watch(isNarrow, (narrow) => applyAutoCollapse(narrow))
  }

  const pageLink = (label: string, to: string): NavigationMenuItem => ({
    label,
    to,
    exact: true,
    class: 'text-sm gap-2',
    onSelect: close,
  })

  const group = (
    label: string,
    icon: string,
    children: NavigationMenuItem[],
    options?: { defaultOpen?: boolean },
  ): NavigationMenuItem => ({
    label,
    icon,
    type: 'trigger',
    defaultOpen: options?.defaultOpen ?? false,
    class: 'mt-1 text-sm gap-2',
    children,
  })

  const routePermissions: Record<string, string> = {
    '/': 'dashboard.view',
    '/meetings/topics': 'meetings.topics.view',
    '/meetings/history': 'meetings.history.view',
    '/records/incoming-documents': 'records.incoming_documents.view',
    '/records/outgoing-documents': 'records.outgoing_documents.view',
    '/records/documents': 'records.documents.view',
    '/records/master-list-requests': 'records.master_list_requests.view',
    '/records/record-logs': 'records.logs.view',
    '/organizations/departments': 'organizations.departments.view',
    '/organizations/companies': 'organizations.companies.view',
    '/organizations/company-purposes': 'organizations.company_purposes.view',
    '/organizations/company-sectors': 'organizations.company_sectors.view',
    '/organizations/officers': 'organizations.officers.view',
    '/portal/file-upload': 'portal.file_upload.view',
    '/portal/google-drive-sync': 'portal.google_drive_sync.view',
    '/portal/portal-logs': 'portal.logs.view',
    '/user-management/roles': 'users.roles.view',
    '/user-management/users': 'users.users.view',
    '/configuration/record-types': 'configuration.record_types.view',
    '/configuration/record-attributes': 'configuration.record_attributes.view',
    '/settings/app-info': 'settings.app_info.view',
    '/settings/app-config': 'settings.app_config.view',
    '/settings/storage': 'settings.storage.view',
  }

  function permittedItem(item: NavigationMenuItem): NavigationMenuItem | null {
    const candidate = item as NavigationMenuItem & { to?: string; children?: NavigationMenuItem[] }
    if (candidate.to) {
      const permission = routePermissions[candidate.to]
      if (permission && !auth.canAccessPage(permission)) return null
    }
    if (candidate.children) {
      const children = candidate.children
        .map(child => permittedItem(child))
        .filter((child): child is NavigationMenuItem => Boolean(child))
      return children.length ? { ...candidate, children } : null
    }
    return candidate
  }

  // Order matches product nav: Dashboard → … → Configuration → Setting
  const links = computed<NavigationMenuItem[][]>(() => [[
    {
      label: t('docetra.navigation.dashboard'),
      icon: 'i-lucide-house',
      to: '/',
      exact: true,
      class: 'text-sm gap-2',
      onSelect: close,
    },
    group(t('docetra.navigation.meeting'), 'i-lucide-video', [
      pageLink(t('docetra.pages.meetingTopic'), '/meetings/topics'),
      pageLink(t('docetra.pages.meetingHistory'), '/meetings/history'),
    ], { defaultOpen: true }),
    group(t('docetra.navigation.record'), 'i-lucide-folder', [
      pageLink(t('docetra.pages.incomingDocument'), '/records/incoming-documents'),
      pageLink(t('docetra.pages.outgoingDocument'), '/records/outgoing-documents'),
      pageLink(t('docetra.pages.document'), '/records/documents'),
      pageLink(t('docetra.pages.masterListRequest'), '/records/master-list-requests'),
      pageLink(t('docetra.pages.recordLog'), '/records/record-logs'),
    ]),
    group(t('docetra.navigation.organization'), 'i-lucide-building-2', [
      pageLink(t('docetra.pages.department'), '/organizations/departments'),
      pageLink(t('docetra.pages.company'), '/organizations/companies'),
      pageLink(t('docetra.pages.companyPurpose'), '/organizations/company-purposes'),
      pageLink(t('docetra.pages.companySector'), '/organizations/company-sectors'),
      pageLink(t('docetra.pages.officer'), '/organizations/officers'),
    ]),
    group(t('docetra.navigation.portal'), 'i-lucide-square-arrow-out-up-right', [
      pageLink(t('docetra.pages.fileUpload'), '/portal/file-upload'),
      pageLink(t('docetra.pages.googleDriveSync'), '/portal/google-drive-sync'),
      pageLink(t('docetra.pages.portalLog'), '/portal/portal-logs'),
    ]),
    group(t('docetra.navigation.userManagement'), 'i-lucide-users', [
      pageLink(t('docetra.pages.role'), '/user-management/roles'),
      pageLink(t('docetra.pages.user'), '/user-management/users'),
    ]),
    group(t('docetra.navigation.configuration'), 'i-lucide-bolt', [
      pageLink(t('docetra.pages.recordType'), '/configuration/record-types'),
      pageLink(t('docetra.pages.recordAttribute'), '/configuration/record-attributes'),
    ]),
    group(t('docetra.navigation.settings'), 'i-lucide-settings', [
      pageLink(t('docetra.pages.appInfo'), '/settings/app-info'),
      pageLink(t('docetra.pages.appConfig'), '/settings/app-config'),
      pageLink(t('docetra.pages.storage'), '/settings/storage'),
    ], { defaultOpen: true }),
  ]
    .map(item => permittedItem(item))
    .filter((item): item is NavigationMenuItem => Boolean(item)), []])

  return {
    open,
    collapsed,
    links,
    close,
    setCollapsed,
  }
}
