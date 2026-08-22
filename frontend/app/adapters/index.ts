import { createEntityAdapter } from './createEntityAdapter'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'

const adapter = <T extends { id: string; stage?: string; updatedAt?: string; createdAt?: string }>(
  endpoint: string,
) => createEntityAdapter<T>({ endpoint })

/** Single adapter factory for any active `record_type.code`. */
export function createRecordAdapter<T extends { id: string; stage?: string; updatedAt?: string; createdAt?: string } = any>(
  typeCode: string,
) {
  return createEntityAdapter<T>({ endpoint: ApiEndpoints.RECORDS(typeCode) })
}

/** Adapter factory for organization orgType (`department` | `company`). */
export function createOrganizationAdapter<T extends { id: string; stage?: string; updatedAt?: string; createdAt?: string } = any>(
  orgType: string,
) {
  return createEntityAdapter<T>({ endpoint: ApiEndpoints.ORGANIZATIONS(orgType) })
}

export const adapters = {
  meetingTopics: createRecordAdapter('meeting_topic'),
  meetingHistory: createRecordAdapter('meeting_history'),
  incomingDocuments: createRecordAdapter('incoming_document'),
  outgoingDocuments: createRecordAdapter('outgoing_document'),
  documents: createRecordAdapter('document'),
  masterListRequests: createRecordAdapter('master_list_request'),
  recordLogs: adapter(ApiEndpoints.RECORD_LOGS),
  departments: createOrganizationAdapter('department'),
  companies: createOrganizationAdapter('company'),
  purposes: adapter(ApiEndpoints.PURPOSE),
  sectors: adapter(ApiEndpoints.SECTOR),
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
