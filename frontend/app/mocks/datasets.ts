import type { DriveFileCatalogItem } from '~/types/docetra/meeting-api'
import type {
  AppRole,
  AppUser,
  Company,
  CompanyPurpose,
  CompanySector,
  DashboardSummary,
  Department,
  FileUploadItem,
  GoogleDriveSyncJob,
  MeetingHistory,
  MeetingTopic,
  Officer,
  PortalLog,
  RecordAttributeConfig,
  RecordDocument,
  RecordLog,
  RecordTypeConfig,
  SystemLog,
} from '~/types/docetra/entities'
import { dateOnly, daysAgo, org, person } from './seed'
import { permissionRowsToFlatKeys } from '~/utils/role/permissions'

function minutesFromNowIso(minutes: number) {
  const d = new Date()
  d.setMinutes(d.getMinutes() + minutes)
  return d.toISOString()
}

export const mockDriveFileCatalog: DriveFileCatalogItem[] = Array.from({ length: 12 }, (_, i) => ({
  id: `pdf_${i + 1}`,
  driveFileId: `gdrive-file-${i + 1}`,
  name: `Synced report ${i + 1}.pdf`,
  mimeType: 'application/pdf',
  sizeBytes: 120_000 + i * 4000,
  syncedAt: daysAgo(i % 5),
  webViewLink: `https://drive.google.com/file/d/mock-${i + 1}/view`,
}))

const meetingStages = ['intake', 'review', 'approval', 'completed'] as const
const recordStages = [
  'created',
  'record_created',
  'observation_note',
  'waiting_related_document',
  'submitted_director',
  'submitted_ddg',
  'submitted_dg',
  'further_measures',
  'reply',
  'finished_final',
] as const
const statuses = ['draft', 'active', 'pending', 'completed', 'archived'] as const

function meetingStage(i: number) {
  return meetingStages[i % meetingStages.length]!
}

function recordStage(i: number) {
  return recordStages[i % recordStages.length]!
}

function status(i: number) {
  return statuses[i % statuses.length]!
}

export const mockMeetingTopics: MeetingTopic[] = Array.from({ length: 24 }, (_, i) => ({
  id: `mt_${i + 1}`,
  title: `Topic ${i + 1}: Quarterly coordination`,
  status: status(i),
  stage: meetingStage(i),
  meetingDate: dateOnly(i % 20),
  recordTime: `${dateOnly(i % 20)}T08:30:00+07:00`,
  tags: i % 2 === 0 ? ['priority'] : ['follow-up'],
  childMeetingCount: (i % 4) + 1,
  childMeetings: Array.from({ length: Math.min(2, (i % 4) + 1) }, (_, j) => ({
    id: `mh_${i}_${j}`,
    title: `Child meeting ${j + 1}`,
    meetingDate: dateOnly(i + j),
  })),
  owner: person(i),
  organization: org(i),
  description: 'Discuss open action items and document follow-up.',
  createdAt: daysAgo(30 - i),
  updatedAt: daysAgo(i % 10),
  attachmentCount: i % 3,
  commentCount: i % 4,
}))

export const mockMeetingHistory: MeetingHistory[] = Array.from({ length: 30 }, (_, i) => {
  const isSoon = i === 0
  const isOnline = i === 0 || i % 4 === 0
  const meetingDate = isSoon
    ? minutesFromNowIso(12)
    : `${dateOnly(i % 25)}T09:00:00+07:00`
  return {
  id: `mh_${i + 1}`,
  title: isSoon ? 'Upcoming coordination (soon)' : `Meeting ${i + 1}`,
  letterNumber: `MTG-${2026}-${String(i + 1).padStart(4, '0')}`,
  letterDate: dateOnly((i + 2) % 25),
  status: status(i),
  stage: meetingStage(i),
  topicId: i % 3 === 0 ? undefined : `mt_${(i % 12) + 1}`,
  topicTitle: i % 3 === 0 ? undefined : `Topic ${(i % 12) + 1}: Quarterly coordination`,
  meetingDate,
  recordTime: meetingDate,
  meetingMode: isOnline ? (i % 8 === 0 ? 'hybrid' : 'online') : 'in_person',
  meetingUrl: isOnline ? 'https://meet.example.com/docetra-room' : undefined,
  durationMinutes: 60,
  seriesId: i === 2 ? 'series_weekly_1' : undefined,
  recurrence: i === 2
    ? { frequency: 'weekly' as const, interval: 1, byWeekday: ['MO'], count: 12 }
    : undefined,
  location: isOnline ? 'Online' : 'Room A',
  attendeesCount: 4 + (i % 8),
  participants: [`Officer ${(i % 5) + 1}`, `Officer ${((i + 1) % 5) + 1}`],
  internalUnits: [`Department ${(i % 4) + 1}`],
  externalUnits: i % 2 === 0 ? [`Partner Company ${(i % 3) + 1}`] : [],
  sortOrder: i % 3 === 0 ? undefined : (i % 5),
  notes: i % 4 === 0
    ? `<h2>Agenda</h2><p>Review progress for meeting ${i + 1}.</p><ul><li>Status updates</li><li>Open actions</li></ul>`
    : '',
  recordContent: i % 4 === 0
    ? `Review progress for meeting ${i + 1}.`
    : undefined,
  tags: i % 2 === 0 ? ['urgent'] : ['follow-up'],
  recordTag: i % 2 === 0 ? 'urgent' : 'follow-up',
  attachmentCount: i % 4,
  owner: person(i),
  createdAt: daysAgo(40 - i),
  updatedAt: daysAgo(i % 8),
}})

function makeRecord(kind: RecordDocument['recordKind'], count: number, prefix: string): RecordDocument[] {
  const typeIdByKind: Record<RecordDocument['recordKind'], string> = {
    incoming: 'rt_incoming',
    outgoing: 'rt_outgoing',
    document: 'rt_document',
    master_list_request: 'rt_master_list',
  }
  const typeNameByKind: Record<RecordDocument['recordKind'], string> = {
    incoming: 'Incoming Document',
    outgoing: 'Outgoing Document',
    document: 'Document',
    master_list_request: 'Master List Request',
  }
  return Array.from({ length: count }, (_, i) => ({
    id: `${prefix}_${i + 1}`,
    referenceNumber: `${prefix.toUpperCase()}-${2026}-${String(i + 1).padStart(4, '0')}`,
    title: `${kind.replace('_', ' ')} record ${i + 1}`,
    recordKind: kind,
    recordFlowCode: 'normal',
    recordTypeId: typeIdByKind[kind],
    recordTypeName: typeNameByKind[kind],
    status: status(i),
    stage: recordStage(i),
    documentType: ['Letter', 'Report', 'Contract', 'Memo'][i % 4],
    senderOrganization: kind === 'incoming' ? org(i) : org(2),
    recipientOrganization: kind === 'outgoing' ? org(i) : org(3),
    receivedDate: kind === 'incoming' ? dateOnly(i % 18) : undefined,
    sentDate: kind === 'outgoing' ? dateOnly(i % 18) : undefined,
    documentDate: kind === 'document' ? dateOnly(i % 18) : undefined,
    letterDate: kind === 'master_list_request' ? dateOnly(i % 18) : undefined,
    letterSubject: `Official letter subject ${i + 1}`,
    directorGeneralDate: kind !== 'master_list_request' ? dateOnly((i + 2) % 18) : undefined,
    directorDate: kind !== 'master_list_request' ? dateOnly((i + 1) % 18) : undefined,
    involvedOfficers: kind !== 'master_list_request' ? [person(i).name, person(i + 1).name] : undefined,
    externalUnits: [org((i + 2) % 5).name],
    officeInCharge: kind === 'master_list_request' ? org((i + 1) % 5).name : undefined,
    officerInCharge: kind === 'master_list_request' ? person(i).name : undefined,
    ownerDepartment: org((i + 1) % 5),
    owner: person(i),
    assignee: person(i + 1),
    waiting: i % 5 === 0,
    description: 'Operational record managed in Docetra.',
    recordContent: 'Operational record managed in Docetra.',
    recordTime: kind === 'incoming'
      ? dateOnly(i % 18)
      : kind === 'outgoing'
        ? dateOnly(i % 18)
        : dateOnly(i % 20),
    details: {
      external_ref: `EXT-${1000 + i}`,
      amount: kind === 'document' || kind === 'master_list_request' ? 1000 + i * 25 : undefined,
    },
    createdAt: daysAgo(50 - i),
    updatedAt: daysAgo(i % 12),
    tags: i % 2 === 0 ? ['urgent'] : ['routine'],
    recordTag: i % 2 === 0 ? 'urgent' : 'routine',
    attachmentCount: i % 4,
    commentCount: i % 5,
  }))
}

export const mockIncomingDocuments = makeRecord('incoming', 36, 'inc')
export const mockOutgoingDocuments = makeRecord('outgoing', 28, 'out')
export const mockDocuments = makeRecord('document', 32, 'doc')
export const mockMasterListRequests = makeRecord('master_list_request', 20, 'mlr')

export const mockRecordLogs: RecordLog[] = Array.from({ length: 40 }, (_, i) => {
  const action = (['created', 'updated', 'stage_changed', 'shared'] as const)[i % 4]!
  const entityTypes = [
    'incoming',
    'outgoing',
    'document',
    'master_list',
    'meeting',
    'meeting_topic',
  ] as const
  const entityType = entityTypes[i % entityTypes.length]!
  const recordNumber = (Math.floor(i / entityTypes.length) % 20) + 1
  const entityPrefix = {
    incoming: 'inc',
    outgoing: 'out',
    document: 'doc',
    master_list: 'mlr',
    meeting: 'mh',
    meeting_topic: 'mt',
  }[entityType]
  const severity = (['info', 'info', 'warn', 'error'] as const)[i % 4]!
  return {
    id: `rl_${i + 1}`,
    status: 'active',
    action,
    entityType,
    entityId: `${entityPrefix}_${recordNumber}`,
    entityTitle: `${entityType.replaceAll('_', ' ')} ${recordNumber}`,
    recordStage: recordStage(i),
    parentRecord: i % 3 === 0 ? `Parent record ${(i % 8) + 1}` : undefined,
    actor: person(i),
    organization: org(i % 5),
    occurredAt: daysAgo(i),
    summary: `Record ${(i % 20) + 1} was ${action.replaceAll('_', ' ')}`,
    category: action === 'shared' ? 'access' : action === 'stage_changed' ? 'workflow' : 'record',
    severity,
    correlationId: `corr_${String(1000 + i)}`,
    changesSummary: action === 'created'
      ? 'Record created'
      : action === 'stage_changed'
        ? 'Stage moved'
        : action === 'shared'
          ? 'Share permissions updated'
          : 'Title / status fields updated',
    createdAt: daysAgo(i),
    updatedAt: daysAgo(i),
  }
})

export const mockDepartments: Department[] = Array.from({ length: 18 }, (_, i) => ({
  id: `dep_${i + 1}`,
  code: `DEP${String(i + 1).padStart(2, '0')}`,
  name: `Department ${i + 1}`,
  status: i % 7 === 0 ? 'disabled' : 'active',
  isActive: i % 7 !== 0,
  parentId: i > 2 ? `dep_${(i % 3) + 1}` : null,
  parentName: i > 2 ? `Department ${(i % 3) + 1}` : undefined,
  taxId: `TAX-${String(10000 + i)}`,
  description: `Operational department ${i + 1}.`,
  address: `${100 + i} Administration Street`,
  contactInfo: `Primary contact for Department ${i + 1}`,
  officerCount: 2 + (i % 6),
  relatedRecordCount: 5 + i,
  contactEmail: `dept${i + 1}@docetra.local`,
  organization: org(2),
  updatedBy: person(i + 1),
  createdAt: daysAgo(100 - i),
  updatedAt: daysAgo(i % 15),
}))

export const mockCompanyPurposes: CompanyPurpose[] = Array.from({ length: 12 }, (_, i) => ({
  id: `pur_${i + 1}`,
  code: `PUR${i + 1}`,
  name: `Purpose ${i + 1}`,
  status: i % 7 === 0 ? 'disabled' : 'active',
  isActive: i % 7 !== 0,
  description: 'Business purpose classification',
  usageCount: i * 3,
  updatedBy: person(i + 1),
  createdAt: daysAgo(80 - i),
  updatedAt: daysAgo(i),
}))

export const mockCompanySectors: CompanySector[] = Array.from({ length: 12 }, (_, i) => ({
  id: `sec_${i + 1}`,
  code: `SEC${i + 1}`,
  name: `Sector ${i + 1}`,
  status: i % 7 === 0 ? 'disabled' : 'active',
  isActive: i % 7 !== 0,
  parentId: i > 2 ? `sec_${(i % 3) + 1}` : null,
  parentName: i > 2 ? `Sector ${(i % 3) + 1}` : undefined,
  description: 'Industry sector classification',
  usageCount: i * 2,
  updatedBy: person(i + 1),
  createdAt: daysAgo(80 - i),
  updatedAt: daysAgo(i),
}))

export const mockCompanies: Company[] = Array.from({ length: 26 }, (_, i) => ({
  id: `co_${i + 1}`,
  code: `CO${String(i + 1).padStart(3, '0')}`,
  name: `Company ${i + 1}`,
  status: i % 8 === 0 ? 'disabled' : 'active',
  isActive: i % 8 !== 0,
  purposeId: `pur_${(i % 12) + 1}`,
  purposeName: `Purpose ${(i % 12) + 1}`,
  sectorId: `sec_${(i % 12) + 1}`,
  sectorName: `Sector ${(i % 12) + 1}`,
  taxId: `TAX-CO-${String(10000 + i)}`,
  registrationNumber: `REG-2020-${1000 + i}`,
  contactEmail: `company${i + 1}@example.com`,
  contactPhone: `+855 23 ${String(100000 + i)}`,
  description: `Company ${i + 1} profile and business description.`,
  address: `${200 + i} Business Avenue`,
  contactInfo: `Primary contact for Company ${i + 1}`,
  relatedRecordCount: i + 2,
  updatedBy: person(i + 1),
  createdAt: daysAgo(90 - i),
  updatedAt: daysAgo(i % 20),
}))

export const mockOfficers: Officer[] = Array.from({ length: 22 }, (_, i) => ({
  id: `off_${i + 1}`,
  code: `OFF${String(i + 1).padStart(3, '0')}`,
  name: person(i).name,
  email: person(i).email,
  phone: `+855 1${i} 234 567`,
  status: i % 8 === 0 ? 'disabled' : 'active',
  isActive: i % 8 !== 0,
  departmentId: `dep_${(i % 18) + 1}`,
  departmentName: `Department ${(i % 18) + 1}`,
  organizationId: `dep_${(i % 18) + 1}`,
  organizationName: `Department ${(i % 18) + 1}`,
  roleId: `role_${(i % 8) + 1}`,
  roleName: ['Administrator', 'Editor', 'Viewer', 'Records Officer', 'Meeting Manager', 'Org Admin', 'Portal Operator', 'Auditor'][i % 8],
  titleRole: ['Officer', 'Manager', 'Director'][i % 3],
  userId: i % 2 === 0 ? `usr_${i + 1}` : undefined,
  authenticationEnabled: i % 2 === 0,
  updatedBy: person(i + 1),
  createdAt: daysAgo(70 - i),
  updatedAt: daysAgo(i % 9),
}))

export const mockRoles: AppRole[] = Array.from({ length: 8 }, (_, i) => {
  const permissionRows = [
    {
      id: `perm_row_${i}_1`,
      documentType: 'incoming_document',
      onlyIfCreator: i % 2 === 0,
      level: i % 3,
      actions: ['view', 'edit', 'create', 'export'].slice(0, 2 + (i % 3)),
    },
    {
      id: `perm_row_${i}_2`,
      documentType: 'meeting_topic',
      onlyIfCreator: false,
      level: 0,
      actions: ['view', 'comment'],
    },
  ]
  return {
    id: `role_${i + 1}`,
    code: ['ADMIN', 'EDITOR', 'VIEWER', 'RECORDS', 'MEETING', 'ORG', 'PORTAL', 'AUDIT'][i]!,
    name: ['Administrator', 'Editor', 'Viewer', 'Records Officer', 'Meeting Manager', 'Org Admin', 'Portal Operator', 'Auditor'][i]!,
    status: 'active',
    description: 'Role permission set for Docetra modules',
    permissionCount: permissionRows.reduce((sum, row) => sum + row.actions.length, 0),
    userCount: 1 + i,
    permissions: permissionRowsToFlatKeys(permissionRows),
    permissionRows,
    permissionSchemaVersion: 1,
    createdAt: daysAgo(120 - i),
    updatedAt: daysAgo(i),
  }
})

export const mockUsers: AppUser[] = Array.from({ length: 16 }, (_, i) => ({
  id: `usr_${i + 1}`,
  name: person(i).name,
  email: person(i).email || `user${i + 1}@docetra.local`,
  status: i % 6 === 0 ? 'disabled' : 'active',
  roleId: `role_${(i % 8) + 1}`,
  roleName: mockRoles[i % 8]!.name,
  officerId: `off_${(i % 22) + 1}`,
  officerName: mockOfficers[i % 22]!.name,
  lastLoginAt: daysAgo(i % 14),
  createdAt: daysAgo(60 - i),
  updatedAt: daysAgo(i % 5),
}))

export const mockRecordTypes: RecordTypeConfig[] = [
  {
    id: 'rt_1',
    code: 'INCOMING',
    name: 'Incoming Document',
    status: 'active',
    description: 'Inbound correspondence workflow',
    workflowEnabled: true,
    stageCount: recordStages.length,
    attributeCount: 6,
    usageCount: 36,
    stages: recordStages.map((code, order) => ({ code, label: code, order })),
    createdAt: daysAgo(200),
    updatedAt: daysAgo(2),
  },
  {
    id: 'rt_2',
    code: 'OUTGOING',
    name: 'Outgoing Document',
    status: 'active',
    workflowEnabled: true,
    stageCount: recordStages.length,
    attributeCount: 5,
    usageCount: 28,
    stages: recordStages.map((code, order) => ({ code, label: code, order })),
    createdAt: daysAgo(200),
    updatedAt: daysAgo(3),
  },
  {
    id: 'rt_3',
    code: 'DOCUMENT',
    name: 'Document',
    status: 'active',
    workflowEnabled: true,
    stageCount: recordStages.length,
    attributeCount: 4,
    usageCount: 32,
    createdAt: daysAgo(180),
    updatedAt: daysAgo(4),
  },
  {
    id: 'rt_4',
    code: 'MASTER_LIST',
    name: 'Master List Request',
    status: 'active',
    workflowEnabled: true,
    stageCount: recordStages.length,
    attributeCount: 3,
    usageCount: 20,
    createdAt: daysAgo(160),
    updatedAt: daysAgo(5),
  },
]

export const mockRecordAttributes: RecordAttributeConfig[] = Array.from({ length: 14 }, (_, i) => ({
  id: `ra_${i + 1}`,
  code: `ATTR_${i + 1}`,
  name: `Attribute ${i + 1}`,
  status: 'active',
  fieldType: ['text', 'date', 'select', 'boolean', 'number'][i % 5]!,
  required: i % 3 === 0,
  usageCount: i + 1,
  createdAt: daysAgo(150 - i),
  updatedAt: daysAgo(i),
}))

export const mockFileUploads: FileUploadItem[] = Array.from({ length: 24 }, (_, i) => ({
  id: `fu_${i + 1}`,
  fileName: `upload-${i + 1}.pdf`,
  name: `upload-${i + 1}.pdf`,
  status: ['completed', 'pending', 'failed', 'active'][i % 4]!,
  mimeType: 'application/pdf',
  sizeBytes: 50_000 + i * 12_000,
  uploader: person(i),
  linkedRecordId: i % 3 === 0 ? undefined : `inc_${(i % 20) + 1}`,
  linkedRecordTitle: i % 3 === 0 ? undefined : `incoming record ${(i % 20) + 1}`,
  storageSource: i % 2 === 0 ? 'local' : 'google_drive',
  progress: i % 4 === 1 ? 62 : 100,
  createdAt: daysAgo(20 - (i % 20)),
  updatedAt: daysAgo(i % 7),
}))

export const mockGoogleDriveSync: GoogleDriveSyncJob[] = Array.from({ length: 10 }, (_, i) => ({
  id: `gds_${i + 1}`,
  name: `Sync folder ${i + 1}`,
  status: ['active', 'completed', 'failed', 'pending'][i % 4]!,
  folderId: `folder_${i + 1}`,
  folderName: `Docetra Folder ${i + 1}`,
  lastSyncAt: daysAgo(i),
  filesSynced: 10 + i * 4,
  errorMessage: i % 4 === 2 ? 'Quota exceeded' : undefined,
  createdAt: daysAgo(40 - i),
  updatedAt: daysAgo(i),
}))

export const mockPortalLogs: PortalLog[] = Array.from({ length: 30 }, (_, i) => ({
  id: `pl_${i + 1}`,
  status: 'active',
  action: ['upload', 'sync', 'download', 'link'][i % 4]!,
  actor: person(i),
  occurredAt: daysAgo(i),
  summary: `Portal ${['upload', 'sync', 'download', 'link'][i % 4]} completed`,
  target: `file-${i + 1}.pdf`,
  createdAt: daysAgo(i),
  updatedAt: daysAgo(i),
}))

export const mockSystemLogs: SystemLog[] = Array.from({ length: 40 }, (_, i) => ({
  id: `sl_${i + 1}`,
  status: 'active',
  level: (['info', 'warn', 'error', 'debug'] as const)[i % 4]!,
  source: ['api', 'worker', 'auth', 'storage'][i % 4]!,
  actionCode: ['CREATE', 'UPDATE', 'READ', 'DELETE'][i % 4]!,
  tableName: ['records', 'files', 'users', 'organizations'][i % 4]!,
  statusCode: [201, 200, 200, 204][i % 4]!,
  sourceLog: ['API', 'Worker', 'Authentication', 'Storage'][i % 4]!,
  ipAddress: `192.168.1.${(i % 240) + 10}`,
  message: `System event ${i + 1}: processed request batch`,
  occurredAt: daysAgo(i % 15),
  correlationId: `corr_${1000 + i}`,
  createdBy: person(i),
  createdAt: daysAgo(i % 15),
  updatedAt: daysAgo(i % 15),
}))

export function getDashboardSummary(): DashboardSummary {
  const meetingEvents = mockMeetingTopics.slice(0, 14).map((topic, i) => ({
    id: `ev_mt_${topic.id}`,
    title: topic.title,
    start: topic.meetingDate || dateOnly(i),
    allDay: true,
    color: (['primary', 'info', 'success', 'warning'] as const)[i % 4],
    type: 'meeting' as const,
    href: `/meetings/topics/${topic.id}`,
    location: i % 2 === 0 ? 'Room A' : 'Online',
  }))

  const deadlineEvents = mockIncomingDocuments
    .filter(r => r.waiting || r.stage === 'waiting_related_document' || r.stage === 'submitted_director')
    .slice(0, 8)
    .map((doc, i) => ({
      id: `ev_dl_${doc.id}`,
      title: doc.title,
      start: doc.receivedDate || dateOnly(i % 12),
      allDay: true,
      color: 'error' as const,
      type: 'deadline' as const,
      href: `/records/incoming-documents/${doc.id}`,
    }))

  const historyEvents = mockMeetingHistory.slice(0, 10).map((m, i) => ({
    id: `ev_mh_${m.id}`,
    title: m.title,
    start: m.meetingDate,
    allDay: true,
    color: 'neutral' as const,
    type: 'meeting' as const,
    href: m.topicId ? `/meetings/topics/${m.topicId}` : '/meetings/history',
    location: m.location,
  }))

  return {
    kpis: [
      { id: 'k1', labelKey: 'docetra.dashboard.kpi.activeRecords', value: 96, trend: 4, href: '/records/documents', updatedAt: daysAgo(0) },
      { id: 'k2', labelKey: 'docetra.dashboard.kpi.waiting', value: 12, trend: -2, href: '/records/incoming-documents?waiting=true', updatedAt: daysAgo(0) },
      { id: 'k3', labelKey: 'docetra.dashboard.kpi.overdue', value: 5, trend: 1, href: '/records/incoming-documents', updatedAt: daysAgo(0) },
      { id: 'k4', labelKey: 'docetra.dashboard.kpi.incoming', value: 36, href: '/records/incoming-documents', updatedAt: daysAgo(0) },
      { id: 'k5', labelKey: 'docetra.dashboard.kpi.outgoing', value: 28, href: '/records/outgoing-documents', updatedAt: daysAgo(0) },
    ],
    workByStage: recordStages.map(s => ({
      stage: s,
      count: mockIncomingDocuments.filter(r => r.stage === s).length
        + mockOutgoingDocuments.filter(r => r.stage === s).length,
    })),
    recordsOverTime: Array.from({ length: 12 }, (_, i) => ({
      date: dateOnly(11 - i),
      count: 4 + ((i * 3) % 9),
    })),
    events: [...meetingEvents, ...deadlineEvents, ...historyEvents],
  }
}
