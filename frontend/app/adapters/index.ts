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
  meetingTopics: adapter(ApiEndpoints.MEETING_TOPICS, mockMeetingTopics, ['title']),
  meetingHistory: adapter(ApiEndpoints.MEETING_HISTORY, mockMeetingHistory, ['title', 'topicTitle', 'location']),
  incomingDocuments: adapter(ApiEndpoints.INCOMING_DOCUMENTS, mockIncomingDocuments, ['title', 'referenceNumber']),
  outgoingDocuments: adapter(ApiEndpoints.OUTGOING_DOCUMENTS, mockOutgoingDocuments, ['title', 'referenceNumber']),
  documents: adapter(ApiEndpoints.DOCUMENTS, mockDocuments, ['title', 'referenceNumber']),
  masterListRequests: adapter(ApiEndpoints.MASTER_LIST_REQUESTS, mockMasterListRequests, ['title', 'referenceNumber']),
  recordLogs: adapter(ApiEndpoints.RECORD_LOGS, mockRecordLogs, ['summary', 'entityTitle', 'action', 'correlationId']),
  departments: adapter(ApiEndpoints.DEPARTMENTS, mockDepartments, ['name', 'code']),
  companies: adapter(ApiEndpoints.COMPANIES, mockCompanies, ['name', 'code', 'registrationNumber']),
  companyPurposes: adapter(ApiEndpoints.COMPANY_PURPOSES, mockCompanyPurposes, ['name', 'code']),
  companySectors: adapter(ApiEndpoints.COMPANY_SECTORS, mockCompanySectors, ['name', 'code']),
  officers: adapter(ApiEndpoints.OFFICERS, mockOfficers, ['name', 'code', 'email']),
  roles: adapter(ApiEndpoints.ROLES, mockRoles, ['name', 'code']),
  users: adapter(ApiEndpoints.USERS, mockUsers, ['name', 'email']),
  recordTypes: adapter(ApiEndpoints.RECORD_TYPES, mockRecordTypes, ['name', 'code']),
  recordAttributes: adapter(ApiEndpoints.RECORD_ATTRIBUTES, mockRecordAttributes, ['name', 'code']),
  fileUploads: adapter(ApiEndpoints.FILE_UPLOADS, mockFileUploads, ['fileName', 'name']),
  googleDriveSync: adapter(ApiEndpoints.GOOGLE_DRIVE_SYNC, mockGoogleDriveSync, ['name', 'folderName']),
  portalLogs: adapter(ApiEndpoints.PORTAL_LOGS, mockPortalLogs, ['summary', 'action', 'target']),
  systemLogs: adapter(ApiEndpoints.SYSTEM_LOGS, mockSystemLogs, ['message', 'source', 'level']),
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
