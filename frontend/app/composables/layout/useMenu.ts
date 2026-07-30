import type { NavigationMenuItem } from '@nuxt/ui'

/** Shared sidebar state and the single source of truth for Docetra navigation. */
export function useMenu() {
  const open = useState('sidebar-open', () => false)
  const { t } = useI18n()

  function close() {
    open.value = false
  }

  const pageLink = (label: string, to: string): NavigationMenuItem => ({
    label,
    to,
    exact: true,
    class: 'text-sm gap-2',
    onSelect: close,
  })

  const links = computed<NavigationMenuItem[][]>(() => [[{
    label: t('docetra.navigation.dashboard'),
    icon: 'i-lucide-layout-dashboard',
    to: '/',
    exact: true,
    class: 'text-sm gap-2',
    onSelect: close,
  }, {
    label: t('docetra.navigation.meeting'),
    icon: 'i-lucide-calendar-days',
    type: 'trigger',
    defaultOpen: true,
    class: 'mt-1 text-sm gap-2',
    children: [
      pageLink(t('docetra.pages.meetingTopic'), '/meetings/topics'),
      pageLink(t('docetra.pages.meetingHistory'), '/meetings/history'),
    ],
  }, {
    label: t('docetra.navigation.record'),
    icon: 'i-lucide-folder',
    type: 'trigger',
    defaultOpen: true,
    class: 'mt-1 text-sm gap-2',
    children: [
      pageLink(t('docetra.pages.incomingDocument'), '/records/incoming-documents'),
      pageLink(t('docetra.pages.outgoingDocument'), '/records/outgoing-documents'),
      pageLink(t('docetra.pages.document'), '/records/documents'),
      pageLink(t('docetra.pages.masterListRequest'), '/records/master-list-requests'),
      pageLink(t('docetra.pages.recordLog'), '/records/logs'),
    ],
  }, {
    label: t('docetra.navigation.organization'),
    icon: 'i-lucide-building-2',
    type: 'trigger',
    defaultOpen: true,
    class: 'mt-1 text-sm gap-2',
    children: [
      pageLink(t('docetra.pages.department'), '/organizations/departments'),
      pageLink(t('docetra.pages.company'), '/organizations/companies'),
      pageLink(t('docetra.pages.companyPurpose'), '/organizations/company-purposes'),
      pageLink(t('docetra.pages.companySector'), '/organizations/company-sectors'),
      pageLink(t('docetra.pages.officer'), '/organizations/officers'),
    ],
  }, {
    label: t('docetra.navigation.userManagement'),
    icon: 'i-lucide-users',
    type: 'trigger',
    defaultOpen: true,
    class: 'mt-1 text-sm gap-2',
    children: [
      pageLink(t('docetra.pages.role'), '/user-management/roles'),
      pageLink(t('docetra.pages.user'), '/user-management/users'),
    ],
  }, {
    label: t('docetra.navigation.configuration'),
    icon: 'i-lucide-sliders-horizontal',
    type: 'trigger',
    defaultOpen: true,
    class: 'mt-1 text-sm gap-2',
    children: [
      pageLink(t('docetra.pages.recordType'), '/configuration/record-types'),
      pageLink(t('docetra.pages.recordAttribute'), '/configuration/record-attributes'),
      pageLink(t('docetra.pages.documentType'), '/configuration/document-types'),
    ],
  }, {
    label: t('docetra.navigation.portal'),
    icon: 'i-lucide-square-arrow-out-up-right',
    type: 'trigger',
    defaultOpen: true,
    class: 'mt-1 text-sm gap-2',
    children: [
      pageLink(t('docetra.pages.fileUpload'), '/portal/file-upload'),
      pageLink(t('docetra.pages.googleDriveSync'), '/portal/google-drive-sync'),
      pageLink(t('docetra.pages.portalLog'), '/portal/logs'),
    ],
  }, {
    label: t('docetra.navigation.systemMonitor'),
    icon: 'i-lucide-square-terminal',
    type: 'trigger',
    defaultOpen: true,
    class: 'mt-1 text-sm gap-2',
    children: [
      pageLink(t('docetra.pages.systemLog'), '/system-monitor/system-logs'),
    ],
  }], []])

  return {
    open,
    links,
    close,
  }
}
