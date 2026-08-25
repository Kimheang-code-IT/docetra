/**
 * Instant-render / offline fallback vocabularies.
 *
 * These TS constants are the seed-parity source: consumers render them
 * immediately (never blocking paint) while `useVocabulary()` merges DB values
 * from GET /api/v2/configuration/enums over them (server wins for
 * labels/order/colors; union by code). Do NOT delete — they are the offline +
 * first-paint source of truth.
 */
import type { VocabularyFallbackOption } from '~/utils/vocabulary'

export const STATUS_OPTIONS_FALLBACK: VocabularyFallbackOption[] = [
  { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
  { label: 'Archived', value: 'archived', labelKey: 'docetra.status.archived' },
  { label: 'Delete', value: 'deleted', labelKey: 'docetra.status.deleted' },
]

export const MEETING_MODE_OPTIONS_FALLBACK: VocabularyFallbackOption[] = [
  { label: 'In person', value: 'in_person', labelKey: 'docetra.meetingModes.in_person' },
  { label: 'Online', value: 'online', labelKey: 'docetra.meetingModes.online' },
  { label: 'Hybrid', value: 'hybrid', labelKey: 'docetra.meetingModes.hybrid' },
]

export const LOG_ACTION_OPTIONS_FALLBACK: VocabularyFallbackOption[] = [
  { label: 'Created', value: 'created', labelKey: 'docetra.logActions.created' },
  { label: 'Updated', value: 'updated', labelKey: 'docetra.logActions.updated' },
  { label: 'Stage changed', value: 'stage_changed', labelKey: 'docetra.logActions.stage_changed' },
  { label: 'Shared', value: 'shared', labelKey: 'docetra.logActions.shared' },
]

export const ENTITY_TYPE_OPTIONS_FALLBACK: VocabularyFallbackOption[] = [
  { label: 'Document', value: 'document', labelKey: 'docetra.entityTypes.document' },
  { label: 'File', value: 'file', labelKey: 'docetra.entityTypes.file' },
  { label: 'Master List Request', value: 'master_list_request', labelKey: 'docetra.entityTypes.master_list_request' },
  { label: 'Meeting', value: 'meeting', labelKey: 'docetra.entityTypes.meeting' },
  { label: 'Meeting Topic', value: 'meeting_topic', labelKey: 'docetra.entityTypes.meeting_topic' },
  { label: 'URL', value: 'url', labelKey: 'docetra.entityTypes.url' },
  { label: 'Approved Master List', value: 'approved_master_list', labelKey: 'docetra.entityTypes.approved_master_list' },
  { label: 'Extension Of Validity', value: 'extension_of_validity', labelKey: 'docetra.entityTypes.extension_of_validity' },
  { label: 'Physical Inspection', value: 'physical_inspection', labelKey: 'docetra.entityTypes.physical_inspection' },
  { label: 'Tax Incentive', value: 'tax_incentive', labelKey: 'docetra.entityTypes.tax_incentive' },
]

export const SEVERITY_OPTIONS_FALLBACK: VocabularyFallbackOption[] = [
  { label: 'Info', value: 'info', labelKey: 'docetra.severity.info' },
  { label: 'Warn', value: 'warn', labelKey: 'docetra.severity.warn' },
  { label: 'Error', value: 'error', labelKey: 'docetra.severity.error' },
]

/** Known vocabulary groups — seeds parity checks and the admin group list. */
export const VOCABULARY_GROUPS = [
  { key: 'status', labelKey: 'docetra.fields.status' },
  { key: 'stage', labelKey: 'docetra.fields.stage' },
  { key: 'meeting_mode', labelKey: 'docetra.fields.meetingMode' },
  { key: 'log_action', labelKey: 'docetra.fields.action' },
  { key: 'severity', labelKey: 'docetra.fields.severity' },
  { key: 'entity_type', labelKey: 'docetra.fields.recordType' },
] as const

/**
 * Filter/field key → vocabulary group. Keys not listed here keep their static
 * schema options.
 */
export const VOCABULARY_GROUP_BY_KEY: Record<string, string> = {
  status: 'status',
  stage: 'stage',
  meetingMode: 'meeting_mode',
  action: 'log_action',
  severity: 'severity',
  entityType: 'entity_type',
}
