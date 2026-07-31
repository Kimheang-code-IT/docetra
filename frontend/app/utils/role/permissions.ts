import type { AppRolePermissionRow } from '~/types/docetra/entities'

/** ERPNext-style permission actions shown in the role matrix. */
export const ROLE_PERMISSION_ACTIONS = [
  'select',
  'read',
  'write',
  'create',
  'delete',
  'print',
  'email',
  'report',
  'import',
  'export',
  'share',
  'mask',
] as const

export type RolePermissionAction = (typeof ROLE_PERMISSION_ACTIONS)[number]

/** Document / module types that can be granted on a role. */
export const ROLE_DOCUMENT_TYPES = [
  { value: 'incoming_document', labelKey: 'docetra.pages.incomingDocument' },
  { value: 'outgoing_document', labelKey: 'docetra.pages.outgoingDocument' },
  { value: 'document', labelKey: 'docetra.pages.document' },
  { value: 'master_list_request', labelKey: 'docetra.pages.masterListRequest' },
  { value: 'meeting_topic', labelKey: 'docetra.pages.meetingTopic' },
  { value: 'meeting_history', labelKey: 'docetra.pages.meetingHistory' },
  { value: 'department', labelKey: 'docetra.pages.department' },
  { value: 'company', labelKey: 'docetra.pages.company' },
  { value: 'officer', labelKey: 'docetra.pages.officer' },
  { value: 'user', labelKey: 'docetra.pages.user' },
  { value: 'role', labelKey: 'docetra.pages.role' },
  { value: 'file_upload', labelKey: 'docetra.pages.fileUpload' },
] as const

export function createEmptyPermissionRow(documentType: string): AppRolePermissionRow {
  return {
    id: `perm_${documentType}_${Date.now().toString(36)}`,
    documentType,
    onlyIfCreator: false,
    level: 0,
    actions: ['read', 'select'],
  }
}

export function permissionRowsToFlatKeys(rows: AppRolePermissionRow[]): string[] {
  const keys: string[] = []
  for (const row of rows) {
    for (const action of row.actions) {
      keys.push(`${row.documentType}:${action}`)
    }
    if (row.onlyIfCreator) keys.push(`${row.documentType}:only_if_creator`)
  }
  return keys
}
