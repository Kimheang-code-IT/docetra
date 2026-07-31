import type { BaseEntity, EntityStatus, PersonSummary, OrganizationSummary } from './common'

export interface MeetingTopic extends BaseEntity {
  title: string
  meetingDate?: string
  childMeetingCount: number
  childMeetings?: Array<{ id: string; title: string; meetingDate?: string; sortOrder?: number }>
  description?: string
}

export interface MeetingHistory extends BaseEntity {
  title: string
  topicId?: string
  topicTitle?: string
  meetingDate: string
  location?: string
  attendeesCount: number
  /** Order within a topic (lower first). */
  sortOrder?: number
  /** TipTap HTML meeting notes. */
  notes?: string
}

export interface RecordDocument extends BaseEntity {
  referenceNumber: string
  title: string
  recordKind: 'incoming' | 'outgoing' | 'document' | 'master_list_request'
  documentType?: string
  senderOrganization?: OrganizationSummary
  recipientOrganization?: OrganizationSummary
  receivedDate?: string
  sentDate?: string
  ownerDepartment?: OrganizationSummary
  waiting?: boolean
  description?: string
}

export interface RecordLog extends BaseEntity {
  action: string
  entityType: string
  entityId: string
  entityTitle: string
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
  code: string
  name: string
  parentId?: string | null
  parentName?: string
  officerCount: number
  relatedRecordCount: number
  contactEmail?: string
  contactPhone?: string
}

export interface Company extends BaseEntity {
  code: string
  name: string
  purposeId?: string
  purposeName?: string
  sectorId?: string
  sectorName?: string
  registrationNumber?: string
  relatedRecordCount: number
}

export interface CompanyPurpose extends BaseEntity {
  code: string
  name: string
  description?: string
  usageCount: number
}

export interface CompanySector extends BaseEntity {
  code: string
  name: string
  description?: string
  usageCount: number
}

export interface Officer extends BaseEntity {
  code: string
  name: string
  email?: string
  phone?: string
  departmentId?: string
  departmentName?: string
  titleRole?: string
  userId?: string
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

export interface DocumentTypeConfig extends BaseEntity {
  code: string
  name: string
  description?: string
  usageCount: number
  allowedMimeTypes?: string
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
  level: 'info' | 'warn' | 'error' | 'debug'
  source: string
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
