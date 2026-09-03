import { createEntityApi } from '~/composables/api/useEntityApi'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { auditToPortalView, auditToSystemView, mapAuditList } from '~/utils/audit/audit-dto'

const entityApi = <T extends { id: string; stage?: string; updatedAt?: string; createdAt?: string }>(
  endpoint: string,
) => createEntityApi<T>({ endpoint })

/** Single API factory for any active `record_type.code`. */
export function createRecordApi<T extends { id: string; stage?: string; updatedAt?: string; createdAt?: string } = any>(
  typeCode: string,
) {
  return createEntityApi<T>({ endpoint: ApiEndpoints.RECORDS(typeCode) })
}

/** API factory for organization orgType (`department` | `company`). */
function createOrganizationApi<T extends { id: string; stage?: string; updatedAt?: string; createdAt?: string } = any>(
  orgType: string,
) {
  return createEntityApi<T>({ endpoint: ApiEndpoints.ORGANIZATIONS(orgType) })
}

export const entityApis = {
  meetingTopics: createRecordApi('meeting_topic'),
  meetingHistory: createRecordApi('meeting_history'),
  incomingDocuments: createRecordApi('incoming_document'),
  outgoingDocuments: createRecordApi('outgoing_document'),
  documents: createRecordApi('document'),
  masterListRequests: createRecordApi('master_list_request'),
  recordLogs: entityApi(ApiEndpoints.RECORD_LOGS),
  departments: createOrganizationApi('department'),
  companies: createOrganizationApi('company'),
  purposes: entityApi(ApiEndpoints.PURPOSE),
  sectors: entityApi(ApiEndpoints.SECTOR),
  officers: entityApi(ApiEndpoints.OFFICERS),
  roles: entityApi(ApiEndpoints.ROLES),
  users: entityApi(ApiEndpoints.USERS),
  recordTypes: entityApi(ApiEndpoints.RECORD_TYPES),
  recordAttributes: entityApi(ApiEndpoints.RECORD_ATTRIBUTES),
  fileUploads: entityApi(ApiEndpoints.FILE_UPLOADS),
  googleDriveSync: entityApi(ApiEndpoints.GOOGLE_DRIVE_SYNC),
  portalLogs: entityApi(ApiEndpoints.PORTAL_LOGS),
  systemLogs: entityApi(ApiEndpoints.SYSTEM_LOGS),
}

const listPortalLogs = entityApis.portalLogs.list.bind(entityApis.portalLogs)
const listSystemLogs = entityApis.systemLogs.list.bind(entityApis.systemLogs)
entityApis.portalLogs.list = (async (query?: Parameters<typeof listPortalLogs>[0]) =>
  mapAuditList(await listPortalLogs(query), auditToPortalView)) as typeof entityApis.portalLogs.list
entityApis.systemLogs.list = (async (query?: Parameters<typeof listSystemLogs>[0]) =>
  mapAuditList(await listSystemLogs(query), auditToSystemView)) as typeof entityApis.systemLogs.list

export type EntityApiKey = keyof typeof entityApis

export function useEntityApis() {
  return entityApis
}
