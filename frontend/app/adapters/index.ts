import { createEntityAdapter } from './createEntityAdapter'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'

const adapter = <T extends { id: string; stage?: string; updatedAt?: string; createdAt?: string }>(
  endpoint: string,
) => createEntityAdapter<T>({ endpoint })

export const adapters = {
  meetingTopics: adapter(ApiEndpoints.MEETING_TOPICS),
  meetingHistory: adapter(ApiEndpoints.MEETING_HISTORY),
  incomingDocuments: adapter(ApiEndpoints.INCOMING_DOCUMENTS),
  outgoingDocuments: adapter(ApiEndpoints.OUTGOING_DOCUMENTS),
  documents: adapter(ApiEndpoints.DOCUMENTS),
  masterListRequests: adapter(ApiEndpoints.MASTER_LIST_REQUESTS),
  recordLogs: adapter(ApiEndpoints.RECORD_LOGS),
  departments: adapter(ApiEndpoints.DEPARTMENTS),
  companies: adapter(ApiEndpoints.COMPANIES),
  companyPurposes: adapter(ApiEndpoints.COMPANY_PURPOSES),
  companySectors: adapter(ApiEndpoints.COMPANY_SECTORS),
  officers: adapter(ApiEndpoints.OFFICERS),
  roles: adapter(ApiEndpoints.ROLES),
  users: adapter(ApiEndpoints.USERS),
  recordTypes: adapter(ApiEndpoints.RECORD_TYPES),
  recordAttributes: adapter(ApiEndpoints.RECORD_ATTRIBUTES),
  fileUploads: adapter(ApiEndpoints.FILE_UPLOADS),
  googleDriveSync: adapter(ApiEndpoints.GOOGLE_DRIVE_SYNC),
  portalLogs: adapter(ApiEndpoints.PORTAL_LOGS),
  systemLogs: adapter(ApiEndpoints.SYSTEM_LOGS),
}

export async function fetchDashboardSummary<T = unknown>() {
  return useApi().get<ApiResponse<T>>(ApiEndpoints.DASHBOARD_SUMMARY, {
    requestKey: 'dashboard-summary',
    cancelPrevious: true,
  })
}

export type AdapterKey = keyof typeof adapters
