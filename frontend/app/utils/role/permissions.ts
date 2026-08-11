import type { AppRolePermissionRow } from '~/types/docetra/entities'

/** Canonical action codes accepted by the future authorization API. */
export const ROLE_PERMISSION_ACTIONS = [
  'view',
  'create',
  'edit',
  'delete',
  'assign',
  'share',
  'export',
  'comment',
  'transition',
  'configure',
] as const

export type RolePermissionAction = (typeof ROLE_PERMISSION_ACTIONS)[number]

export interface RoleDocumentTypeDefinition {
  value: string
  labelKey: string
  permissionPrefix: string
  actions: readonly RolePermissionAction[]
}

/** Matrix rows map to the same namespace used by page and API authorization. */
const WORKFLOW_ACTIONS: readonly RolePermissionAction[] = ['view', 'create', 'edit', 'delete', 'assign', 'share', 'export', 'comment', 'transition']
const MASTER_DATA_ACTIONS: readonly RolePermissionAction[] = ['view', 'create', 'edit', 'delete', 'export', 'comment']
const AUDIT_ACTIONS: readonly RolePermissionAction[] = ['view', 'export']
const CONFIG_ACTIONS: readonly RolePermissionAction[] = ['view', 'create', 'edit', 'delete', 'comment', 'configure']
export const ROLE_DOCUMENT_TYPES: readonly RoleDocumentTypeDefinition[] = [
  { value: 'incoming_document', labelKey: 'docetra.pages.incomingDocument', permissionPrefix: 'records.incoming_documents', actions: WORKFLOW_ACTIONS },
  { value: 'outgoing_document', labelKey: 'docetra.pages.outgoingDocument', permissionPrefix: 'records.outgoing_documents', actions: WORKFLOW_ACTIONS },
  { value: 'document', labelKey: 'docetra.pages.document', permissionPrefix: 'records.documents', actions: WORKFLOW_ACTIONS },
  { value: 'master_list_request', labelKey: 'docetra.pages.masterListRequest', permissionPrefix: 'records.master_list_requests', actions: WORKFLOW_ACTIONS },
  { value: 'meeting_topic', labelKey: 'docetra.pages.meetingTopic', permissionPrefix: 'meetings.topics', actions: WORKFLOW_ACTIONS },
  { value: 'meeting_history', labelKey: 'docetra.pages.meetingHistory', permissionPrefix: 'meetings.history', actions: WORKFLOW_ACTIONS },
  { value: 'department', labelKey: 'docetra.pages.department', permissionPrefix: 'organizations.departments', actions: MASTER_DATA_ACTIONS },
  { value: 'company', labelKey: 'docetra.pages.company', permissionPrefix: 'organizations.companies', actions: MASTER_DATA_ACTIONS },
  { value: 'company_purpose', labelKey: 'docetra.pages.companyPurpose', permissionPrefix: 'organizations.company_purposes', actions: MASTER_DATA_ACTIONS },
  { value: 'company_sector', labelKey: 'docetra.pages.companySector', permissionPrefix: 'organizations.company_sectors', actions: MASTER_DATA_ACTIONS },
  { value: 'officer', labelKey: 'docetra.pages.officer', permissionPrefix: 'organizations.officers', actions: MASTER_DATA_ACTIONS },
  { value: 'user', labelKey: 'docetra.pages.user', permissionPrefix: 'users.users', actions: ['view', 'create', 'edit', 'delete', 'configure'] },
  { value: 'role', labelKey: 'docetra.pages.role', permissionPrefix: 'users.roles', actions: ['view', 'create', 'edit', 'delete', 'configure'] },
  { value: 'record_type', labelKey: 'docetra.pages.recordType', permissionPrefix: 'configuration.record_types', actions: CONFIG_ACTIONS },
  { value: 'record_attribute', labelKey: 'docetra.pages.recordAttribute', permissionPrefix: 'configuration.record_attributes', actions: CONFIG_ACTIONS },
  { value: 'record_log', labelKey: 'docetra.pages.recordLog', permissionPrefix: 'records.logs', actions: AUDIT_ACTIONS },
  { value: 'file_upload', labelKey: 'docetra.pages.fileUpload', permissionPrefix: 'portal.file_upload', actions: ['view', 'create', 'delete', 'share', 'export'] },
  { value: 'google_drive_sync', labelKey: 'docetra.pages.googleDriveSync', permissionPrefix: 'portal.google_drive_sync', actions: CONFIG_ACTIONS },
  { value: 'portal_log', labelKey: 'docetra.pages.portalLog', permissionPrefix: 'portal.logs', actions: AUDIT_ACTIONS },
  { value: 'system_log', labelKey: 'docetra.pages.systemLog', permissionPrefix: 'system.logs', actions: AUDIT_ACTIONS },
  { value: 'app_config', labelKey: 'docetra.pages.appConfig', permissionPrefix: 'settings.app_config', actions: ['view', 'edit', 'configure'] },
  { value: 'app_info', labelKey: 'docetra.pages.appInfo', permissionPrefix: 'settings.app_info', actions: ['view', 'edit', 'configure'] },
  { value: 'storage', labelKey: 'docetra.pages.storage', permissionPrefix: 'settings.storage', actions: ['view', 'edit', 'configure'] },
] as const

const ACTION_SET = new Set<string>(ROLE_PERMISSION_ACTIONS)
const LEGACY_ACTION_MAP: Record<string, RolePermissionAction | undefined> = {
  select: 'view',
  read: 'view',
  write: 'edit',
  email: 'comment',
  report: 'view',
  import: 'create',
  mask: 'view',
}

export function normalizePermissionActions(actions: readonly string[] | null | undefined): RolePermissionAction[] {
  const normalized = new Set<RolePermissionAction>()
  for (const raw of actions || []) {
    const action = ACTION_SET.has(raw)
      ? raw as RolePermissionAction
      : LEGACY_ACTION_MAP[raw]
    if (action) normalized.add(action)
  }
  if ([...normalized].some(action => action !== 'view')) normalized.add('view')
  return ROLE_PERMISSION_ACTIONS.filter(action => normalized.has(action))
}

export function createEmptyPermissionRow(documentType: string): AppRolePermissionRow {
  return {
    id: `perm_${documentType}`,
    documentType,
    onlyIfCreator: false,
    level: 0,
    actions: [],
  }
}

/** Merge API rows with the current matrix catalog and discard unknown rows/actions. */
export function normalizePermissionRows(
  rows: readonly AppRolePermissionRow[] | null | undefined,
  includeEmpty = true,
): AppRolePermissionRow[] {
  const byType = new Map((rows || []).map(row => [row.documentType, row]))
  const normalized = ROLE_DOCUMENT_TYPES.map((definition) => {
    const existing = byType.get(definition.value)
    const actions = normalizePermissionActions(existing?.actions)
      .filter(action => definition.actions.includes(action))
    return {
      id: existing?.id || `perm_${definition.value}`,
      documentType: definition.value,
      onlyIfCreator: actions.length ? Boolean(existing?.onlyIfCreator) : false,
      level: Math.min(9, Math.max(0, Number(existing?.level || 0))),
      actions,
    }
  })
  return includeEmpty ? normalized : normalized.filter(row => row.actions.length > 0)
}

/** Enforce action dependencies consistently for checkbox and API payload flows. */
export function setPermissionAction(
  row: AppRolePermissionRow,
  action: string,
  enabled: boolean,
): AppRolePermissionRow {
  const normalizedAction = ACTION_SET.has(action)
    ? action as RolePermissionAction
    : LEGACY_ACTION_MAP[action]
  if (!normalizedAction) return row
  const actions = new Set(normalizePermissionActions(row.actions))
  if (enabled) {
    actions.add(normalizedAction)
    actions.add('view')
  }
  else if (normalizedAction === 'view') {
    actions.clear()
  }
  else {
    actions.delete(normalizedAction)
  }
  const ordered = ROLE_PERMISSION_ACTIONS.filter(item => actions.has(item))
  return {
    ...row,
    actions: ordered,
    onlyIfCreator: ordered.length ? Boolean(row.onlyIfCreator) : false,
  }
}

/** Expanded capabilities sent with structured rows for fast authorization checks. */
export function permissionRowsToFlatKeys(rows: AppRolePermissionRow[]): string[] {
  const definitions = new Map(ROLE_DOCUMENT_TYPES.map(item => [item.value, item]))
  const keys = new Set<string>()
  for (const row of normalizePermissionRows(rows, false)) {
    const prefix = definitions.get(row.documentType)?.permissionPrefix
    if (!prefix) continue
    for (const action of row.actions) keys.add(`${prefix}.${action}`)
  }
  return [...keys].sort()
}
