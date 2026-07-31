import { createEntityAdapter, createStore } from './createEntityAdapter'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import {
  getDashboardSummary,
  mockCompanies,
  mockCompanyPurposes,
  mockCompanySectors,
  mockDepartments,
  mockDocumentTypes,
  mockDocuments,
  mockFileUploads,
  mockGoogleDriveSync,
  mockIncomingDocuments,
  mockMasterListRequests,
  mockMeetingHistory,
  mockMeetingTopics,
  mockOfficers,
  mockOutgoingDocuments,
  mockPortalLogs,
  mockRecordAttributes,
  mockRecordLogs,
  mockRecordTypes,
  mockRoles,
  mockSystemLogs,
  mockUsers,
} from '~/mocks/datasets'
import { mockLatency, ok } from '~/mocks/query'
import { createId, nowIso, person } from '~/mocks/seed'
import type { RecordDocument } from '~/types/docetra/entities'

const meetingTopics = createStore(mockMeetingTopics)
const meetingHistory = createStore(mockMeetingHistory)
const incoming = createStore(mockIncomingDocuments)
const outgoing = createStore(mockOutgoingDocuments)
const documents = createStore(mockDocuments)
const masterList = createStore(mockMasterListRequests)
const recordLogs = createStore(mockRecordLogs)
const departments = createStore(mockDepartments)
const companies = createStore(mockCompanies)
const purposes = createStore(mockCompanyPurposes)
const sectors = createStore(mockCompanySectors)
const officers = createStore(mockOfficers)
const roles = createStore(mockRoles)
const users = createStore(mockUsers)
const recordTypes = createStore(mockRecordTypes)
const recordAttributes = createStore(mockRecordAttributes)
const documentTypes = createStore(mockDocumentTypes)
const fileUploads = createStore(mockFileUploads)
const driveSync = createStore(mockGoogleDriveSync)
const portalLogs = createStore(mockPortalLogs)
const systemLogs = createStore(mockSystemLogs)

function recordDefaults(kind: RecordDocument['recordKind'], prefix: string) {
  return (payload: Partial<RecordDocument>): RecordDocument => ({
    id: createId(prefix),
    referenceNumber: payload.referenceNumber || `${prefix.toUpperCase()}-${Date.now()}`,
    title: payload.title || 'Untitled',
    recordKind: kind,
    status: payload.status || 'draft',
    stage: payload.stage || 'intake',
    documentType: payload.documentType,
    senderOrganization: payload.senderOrganization,
    recipientOrganization: payload.recipientOrganization,
    receivedDate: payload.receivedDate,
    sentDate: payload.sentDate,
    ownerDepartment: payload.ownerDepartment,
    owner: payload.owner || person(0),
    assignee: payload.assignee,
    waiting: payload.waiting || false,
    description: payload.description,
    createdAt: nowIso(),
    updatedAt: nowIso(),
    attachmentCount: 0,
    commentCount: 0,
    tags: payload.tags || [],
  })
}

export const adapters = {
  meetingTopics: createEntityAdapter({
    endpoint: ApiEndpoints.MEETING_TOPICS,
    store: meetingTopics,
    searchKeys: ['title'],
    createDefaults: payload => ({
      id: createId('mt'),
      title: payload.title || 'New topic',
      status: payload.status || 'draft',
      stage: payload.stage || 'intake',
      meetingDate: payload.meetingDate,
      childMeetingCount: 0,
      childMeetings: [],
      owner: payload.owner || person(0),
      organization: payload.organization,
      description: payload.description,
      createdAt: nowIso(),
      updatedAt: nowIso(),
      attachmentCount: 0,
      commentCount: 0,
    }),
  }),
  meetingHistory: createEntityAdapter({
    endpoint: ApiEndpoints.MEETING_HISTORY,
    store: meetingHistory,
    searchKeys: ['title', 'topicTitle', 'location'],
  }),
  incomingDocuments: createEntityAdapter({
    endpoint: ApiEndpoints.INCOMING_DOCUMENTS,
    store: incoming,
    searchKeys: ['title', 'referenceNumber'],
    createDefaults: recordDefaults('incoming', 'inc'),
  }),
  outgoingDocuments: createEntityAdapter({
    endpoint: ApiEndpoints.OUTGOING_DOCUMENTS,
    store: outgoing,
    searchKeys: ['title', 'referenceNumber'],
    createDefaults: recordDefaults('outgoing', 'out'),
  }),
  documents: createEntityAdapter({
    endpoint: ApiEndpoints.DOCUMENTS,
    store: documents,
    searchKeys: ['title', 'referenceNumber'],
    createDefaults: recordDefaults('document', 'doc'),
  }),
  masterListRequests: createEntityAdapter({
    endpoint: ApiEndpoints.MASTER_LIST_REQUESTS,
    store: masterList,
    searchKeys: ['title', 'referenceNumber'],
    createDefaults: recordDefaults('master_list_request', 'mlr'),
  }),
  recordLogs: createEntityAdapter({
    endpoint: ApiEndpoints.RECORD_LOGS,
    store: recordLogs,
    searchKeys: ['summary', 'entityTitle', 'action', 'entityType', 'correlationId'],
  }),
  departments: createEntityAdapter({
    endpoint: ApiEndpoints.DEPARTMENTS,
    store: departments,
    searchKeys: ['name', 'code'],
    createDefaults: payload => ({
      id: createId('dep'),
      code: payload.code || `DEP${Date.now().toString().slice(-4)}`,
      name: payload.name || 'New department',
      status: payload.status || 'active',
      parentId: payload.parentId ?? null,
      parentName: payload.parentName,
      officerCount: 0,
      relatedRecordCount: 0,
      contactEmail: payload.contactEmail,
      createdAt: nowIso(),
      updatedAt: nowIso(),
    }),
  }),
  companies: createEntityAdapter({
    endpoint: ApiEndpoints.COMPANIES,
    store: companies,
    searchKeys: ['name', 'code', 'registrationNumber'],
    createDefaults: payload => ({
      id: createId('co'),
      code: payload.code || `CO${Date.now().toString().slice(-4)}`,
      name: payload.name || 'New company',
      status: payload.status || 'active',
      purposeId: payload.purposeId,
      purposeName: payload.purposeName,
      sectorId: payload.sectorId,
      sectorName: payload.sectorName,
      registrationNumber: payload.registrationNumber,
      relatedRecordCount: 0,
      createdAt: nowIso(),
      updatedAt: nowIso(),
    }),
  }),
  companyPurposes: createEntityAdapter({
    endpoint: ApiEndpoints.COMPANY_PURPOSES,
    store: purposes,
    searchKeys: ['name', 'code'],
  }),
  companySectors: createEntityAdapter({
    endpoint: ApiEndpoints.COMPANY_SECTORS,
    store: sectors,
    searchKeys: ['name', 'code'],
  }),
  officers: createEntityAdapter({
    endpoint: ApiEndpoints.OFFICERS,
    store: officers,
    searchKeys: ['name', 'code', 'email'],
  }),
  roles: createEntityAdapter({
    endpoint: ApiEndpoints.ROLES,
    store: roles,
    searchKeys: ['name', 'code'],
  }),
  users: createEntityAdapter({
    endpoint: ApiEndpoints.USERS,
    store: users,
    searchKeys: ['name', 'email'],
  }),
  recordTypes: createEntityAdapter({
    endpoint: ApiEndpoints.RECORD_TYPES,
    store: recordTypes,
    searchKeys: ['name', 'code'],
  }),
  recordAttributes: createEntityAdapter({
    endpoint: ApiEndpoints.RECORD_ATTRIBUTES,
    store: recordAttributes,
    searchKeys: ['name', 'code'],
  }),
  documentTypes: createEntityAdapter({
    endpoint: ApiEndpoints.DOCUMENT_TYPES,
    store: documentTypes,
    searchKeys: ['name', 'code'],
  }),
  fileUploads: createEntityAdapter({
    endpoint: ApiEndpoints.FILE_UPLOADS,
    store: fileUploads,
    searchKeys: ['fileName', 'name', 'linkedRecordTitle'],
  }),
  googleDriveSync: createEntityAdapter({
    endpoint: ApiEndpoints.GOOGLE_DRIVE_SYNC,
    store: driveSync,
    searchKeys: ['name', 'folderName'],
  }),
  portalLogs: createEntityAdapter({
    endpoint: ApiEndpoints.PORTAL_LOGS,
    store: portalLogs,
    searchKeys: ['summary', 'action', 'target'],
  }),
  systemLogs: createEntityAdapter({
    endpoint: ApiEndpoints.SYSTEM_LOGS,
    store: systemLogs,
    searchKeys: ['message', 'source', 'level'],
  }),
}

export async function fetchDashboardSummary() {
  const config = useRuntimeConfig()
  if (config.public.useMockData !== false) {
    await mockLatency(null)
    return ok(getDashboardSummary())
  }
  const api = useApi()
  return await api.get(ApiEndpoints.DASHBOARD_SUMMARY)
}

export type AdapterKey = keyof typeof adapters
