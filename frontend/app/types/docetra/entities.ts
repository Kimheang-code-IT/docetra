import type { BaseEntity, EntityStatus, PersonSummary, OrganizationSummary } from './common'
import type { MeetingBoardTiming, MeetingMode, MeetingRecurrenceRule } from './meeting-api'

export interface MeetingTopic extends BaseEntity {
  title: string
  /** Business timestamp for ordering and timeline views. */
  recordTime?: string
  meetingDate?: string
  childMeetingCount: number
  childMeetings?: Array<{ id: string; title: string; meetingDate?: string; sortOrder?: number }>
  description?: string
}

export interface MeetingHistory extends BaseEntity, MeetingBoardTiming {
  title: string
  letterNumber: string
  letterDate: string
  topicId?: string
  topicTitle?: string
  meetingDate: string
  meetingMode?: MeetingMode
  meetingUrl?: string
  durationMinutes?: number
  seriesId?: string
  recurrence?: MeetingRecurrenceRule
  isRecurrenceException?: boolean
  location?: string
  attendeesCount?: number
  participants?: string[]
  internalUnits?: string[]
  externalUnits?: string[]
  /** Order within a topic (lower first). */
  sortOrder?: number
  /** TipTap HTML / record content (`record_content`). */
  notes?: string
  recordContent?: string
  /** Business timestamp (`record_time`); falls back to `meetingDate` in UI. */
  recordTime?: string
  /** Tags as comma text (`record_tag`); arrays also on `tags`. */
  recordTag?: string
}

export interface RecordDocument extends BaseEntity {
  referenceNumber: string
  title: string
  recordKind: 'incoming' | 'outgoing' | 'document' | 'master_list_request'
  recordFlowCode?: string
  /** Configured Record Type id (Configuration → Record Types). */
  recordTypeId?: string
  /** Denormalized Record Type name for list/board display. */
  recordTypeName?: string
  senderOrganization?: OrganizationSummary
  recipientOrganization?: OrganizationSummary
  receivedDate?: string
  sentDate?: string
  documentDate?: string
  letterDate?: string
  letterSubject?: string
  directorGeneralDate?: string
  directorDate?: string
  /** Company id used as document-type classification on Incoming Document forms. */
  documentType?: string
  involvedOfficers?: string[]
  externalUnits?: string[]
  /** Department id (Involved Office) on Incoming Document forms. */
  officeInCharge?: string
  officerInCharge?: string
  /** Record business timestamp (`record_time`). */
  recordTime?: string
  ownerDepartment?: OrganizationSummary
  waiting?: boolean
  /** Main content (`record_content`); falls back from `description` in UI. */
  recordContent?: string
  description?: string
  /** Tags as comma text (`record_tag`); arrays also accepted. */
  recordTag?: string
  /** Dynamic attribute values keyed by attribute code (`record_detail`). */
  details?: Record<string, unknown>
}

export interface RecordLog extends BaseEntity {
  /** Sequential number assigned for the current paginated table. */
  rowNumber?: number
  action: string
  entityType: string
  entityId: string
  entityTitle: string
  recordStage?: string
  parentRecord?: string
  actor?: PersonSummary
  organization?: OrganizationSummary
  occurredAt: string
  summary: string
  category?: string
  severity?: 'info' | 'warn' | 'error'
  correlationId?: string
  /** Safe human-readable change summary (never raw secrets). */
  changesSummary?: string
}

export interface Department extends BaseEntity {
  rowNumber?: number
  code?: string
  name: string
  parentId?: string | null
  parentName?: string
  isActive?: boolean
  taxId?: string
  description?: string
  address?: string
  contactInfo?: string
  logoUrl?: string
  officerCount: number
  relatedRecordCount: number
  contactEmail?: string
  contactPhone?: string
}

export interface Company extends BaseEntity {
  rowNumber?: number
  code?: string
  name: string
  purposeId?: string
  purposeName?: string
  sectorId?: string
  sectorName?: string
  taxId?: string
  registrationNumber?: string
  isActive?: boolean
  contactEmail?: string
  contactPhone?: string
  description?: string
  address?: string
  contactInfo?: string
  logoUrl?: string
  relatedRecordCount: number
}

export interface CompanyPurpose extends BaseEntity {
  rowNumber?: number
  code?: string
  name: string
  description?: string
  isActive?: boolean
  usageCount?: number
}

export interface CompanySector extends BaseEntity {
  rowNumber?: number
  code?: string
  name: string
  description?: string
  isActive?: boolean
  parentId?: string | null
  parentName?: string
  usageCount?: number
}

export interface Officer extends BaseEntity {
  rowNumber?: number
  code?: string
  name: string
  email?: string
  phone?: string
  departmentId?: string
  departmentName?: string
  titleRole?: string
  userId?: string
  organizationId?: string
  organizationName?: string
  roleId?: string
  roleName?: string
  isActive?: boolean
  authenticationEnabled?: boolean
}

export interface AppRolePermissionRow {
  id: string
  documentType: string
  onlyIfCreator?: boolean
  level?: number
  actions: string[]
}

export interface AppRole extends BaseEntity {
  code: string
  name: string
  description?: string
  permissionCount: number
  userCount: number
  permissions?: string[]
  permissionRows?: AppRolePermissionRow[]
}

export interface AppUser extends BaseEntity {
  name: string
  email: string
  roleId?: string
  roleName?: string
  officerId?: string
  officerName?: string
  lastLoginAt?: string
  status: EntityStatus
}

export interface RecordTypeConfig extends BaseEntity {
  code: string
  name: string
  description?: string
  workflowEnabled: boolean
  stageCount: number
  attributeCount: number
  usageCount: number
  stages?: Array<{ code: string; label: string; order: number }>
}

export interface RecordAttributeConfig extends BaseEntity {
  code: string
  name: string
  fieldType: string
  required: boolean
  usageCount: number
  optionsJson?: string
}

export interface FileUploadItem extends BaseEntity {
  fileName: string
  mimeType: string
  sizeBytes: number
  uploader?: PersonSummary
  linkedRecordId?: string
  linkedRecordTitle?: string
  storageSource: 'local' | 'google_drive'
  progress?: number
}

export interface GoogleDriveSyncJob extends BaseEntity {
  name: string
  folderId?: string
  folderName?: string
  lastSyncAt?: string
  filesSynced: number
  errorMessage?: string
}

export interface PortalLog extends BaseEntity {
  action: string
  actor?: PersonSummary
  occurredAt: string
  summary: string
  target?: string
}

export interface SystemLog extends BaseEntity {
  rowNumber?: number
  level: 'info' | 'warn' | 'error' | 'debug'
  source: string
  actionCode?: string
  tableName?: string
  statusCode?: number
  sourceLog?: string
  ipAddress?: string
  message: string
  occurredAt: string
  correlationId?: string
}

export interface DashboardKpi {
  id: string
  labelKey: string
  value: number
  trend?: number
  href?: string
  updatedAt: string
}

export interface DashboardCalendarEvent {
  id: string
  title: string
  /** ISO date (`YYYY-MM-DD`) or datetime */
  start: string
  end?: string
  allDay?: boolean
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'neutral'
  type?: 'meeting' | 'deadline' | 'record' | 'upload'
  href?: string
  location?: string
}

export interface DashboardSummary {
  kpis: DashboardKpi[]
  workByStage: Array<{ stage: string; count: number }>
  recordsOverTime: Array<{ date: string; count: number }>
  events: DashboardCalendarEvent[]
}
