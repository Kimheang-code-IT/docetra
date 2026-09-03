/**
 * Static select/filter options for status, meeting mode, action, severity and
 * entity type. These are the single source for list filters and form select
 * fields (the DB vocabulary feature was removed by product decision).
 */
export interface SelectOption {
  label: string
  value: string
  labelKey?: string
  color?: string
}

export const STATUS_OPTIONS: SelectOption[] = [
  { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
  { label: 'Archived', value: 'archived', labelKey: 'docetra.status.archived' },
  { label: 'Delete', value: 'deleted', labelKey: 'docetra.status.deleted' },
]

export const MEETING_MODE_OPTIONS: SelectOption[] = [
  { label: 'In person', value: 'in_person', labelKey: 'docetra.meetingModes.in_person' },
  { label: 'Online', value: 'online', labelKey: 'docetra.meetingModes.online' },
  { label: 'Hybrid', value: 'hybrid', labelKey: 'docetra.meetingModes.hybrid' },
]

export const LOG_ACTION_OPTIONS: SelectOption[] = [
  { label: 'Created', value: 'created', labelKey: 'docetra.logActions.created' },
  { label: 'Updated', value: 'updated', labelKey: 'docetra.logActions.updated' },
  { label: 'Stage changed', value: 'stage_changed', labelKey: 'docetra.logActions.stage_changed' },
  { label: 'Shared', value: 'shared', labelKey: 'docetra.logActions.shared' },
]

export const ENTITY_TYPE_OPTIONS: SelectOption[] = [
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

export const SEVERITY_OPTIONS: SelectOption[] = [
  { label: 'Info', value: 'info', labelKey: 'docetra.severity.info' },
  { label: 'Warn', value: 'warn', labelKey: 'docetra.severity.warn' },
  { label: 'Error', value: 'error', labelKey: 'docetra.severity.error' },
]
