import { createEntityAdapter, createMockStore } from './createEntityAdapter'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'
import {
  getDashboardSummary,
  mockCompanies,
  mockCompanyPurposes,
  mockCompanySectors,
  mockDepartments,
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

const adapter = <T extends { id: string; stage?: string; updatedAt?: string; createdAt?: string }>(
  endpoint: string,
  seed: T[],
  searchKeys?: string[],
) => createEntityAdapter({ endpoint, store: createMockStore(seed), searchKeys })

export const adapters = {
  meetingTopics: adapter(ApiEndpoints.MEETING_TOPICS, mockMeetingTopics, ['title', 'recordTime', 'recordTag']),
  meetingHistory: adapter(ApiEndpoints.MEETING_HISTORY, mockMeetingHistory, [
    'title',
    'letterNumber',
    'topicTitle',
    'location',
    'participants',
    'internalUnits',
    'externalUnits',
    'recordTag',
  ]),
  incomingDocuments: adapter(ApiEndpoints.INCOMING_DOCUMENTS, mockIncomingDocuments, [
    'title', 'referenceNumber', 'letterSubject', 'involvedOfficers', 'externalUnits', 'recordTag',
  ]),
  outgoingDocuments: adapter(ApiEndpoints.OUTGOING_DOCUMENTS, mockOutgoingDocuments, [
    'title', 'referenceNumber', 'letterSubject', 'involvedOfficers', 'externalUnits', 'recordTag',
  ]),
  documents: adapter(ApiEndpoints.DOCUMENTS, mockDocuments, [
    'title', 'referenceNumber', 'letterSubject', 'involvedOfficers', 'externalUnits', 'recordTag',
  ]),
  masterListRequests: adapter(ApiEndpoints.MASTER_LIST_REQUESTS, mockMasterListRequests, [
    'title', 'referenceNumber', 'letterSubject', 'officeInCharge', 'officerInCharge', 'externalUnits', 'recordTag',
  ]),
  recordLogs: adapter(ApiEndpoints.RECORD_LOGS, mockRecordLogs, ['summary', 'entityTitle', 'action', 'correlationId']),
  departments: adapter(ApiEndpoints.DEPARTMENTS, mockDepartments, [
    'name', 'code', 'taxId', 'contactEmail', 'contactPhone', 'address', 'contactInfo',
  ]),
  companies: adapter(ApiEndpoints.COMPANIES, mockCompanies, [
    'name', 'code', 'taxId', 'registrationNumber', 'sectorName', 'purposeName',
    'contactEmail', 'contactPhone', 'address', 'contactInfo',
  ]),
  companyPurposes: adapter(ApiEndpoints.COMPANY_PURPOSES, mockCompanyPurposes, ['name', 'code', 'description']),
  companySectors: adapter(ApiEndpoints.COMPANY_SECTORS, mockCompanySectors, ['name', 'code', 'description', 'parentName']),
  officers: adapter(ApiEndpoints.OFFICERS, mockOfficers, [
    'name', 'code', 'email', 'organizationName', 'roleName',
  ]),
  roles: adapter(ApiEndpoints.ROLES, mockRoles, ['name', 'code']),
  users: adapter(ApiEndpoints.USERS, mockUsers, ['name', 'email']),
  recordTypes: adapter(ApiEndpoints.RECORD_TYPES, mockRecordTypes, ['name', 'code']),
  recordAttributes: adapter(ApiEndpoints.RECORD_ATTRIBUTES, mockRecordAttributes, ['name', 'code']),
  fileUploads: adapter(ApiEndpoints.FILE_UPLOADS, mockFileUploads, ['fileName', 'name']),
  googleDriveSync: adapter(ApiEndpoints.GOOGLE_DRIVE_SYNC, mockGoogleDriveSync, ['name', 'folderName']),
  portalLogs: adapter(ApiEndpoints.PORTAL_LOGS, mockPortalLogs, ['summary', 'action', 'target']),
  systemLogs: adapter(ApiEndpoints.SYSTEM_LOGS, mockSystemLogs, [
    'message', 'source', 'level', 'actionCode', 'tableName', 'sourceLog', 'ipAddress',
  ]),
}

export async function fetchDashboardSummary<T = ReturnType<typeof getDashboardSummary>>() {
  if (useRuntimeConfig().public.useMockData !== false) {
    await mockLatency(null)
    return ok(getDashboardSummary()) as ApiResponse<T>
  }
  return useApi().get<ApiResponse<T>>(ApiEndpoints.DASHBOARD_SUMMARY, {
    requestKey: 'dashboard-summary',
    cancelPrevious: true,
  })
}

export type AdapterKey = keyof typeof adapters
