export const ApiEndpoints = {
    AUTH_LOGIN: '/api/v2/auth/login',
    AUTH_REGISTER: '/api/v2/auth/register',
    AUTH_BOOTSTRAP: '/api/v2/auth/bootstrap',
    AUTH_LOGOUT: '/api/v2/auth/logout',
  AUTH_ME: '/api/v2/auth/me',
  AUTH_REFRESH: '/api/v2/auth/refresh',
  AUTH_FORGOT_PASSWORD: '/api/v2/auth/forgot-password',
  AUTH_RESET_VERIFY: '/api/v2/auth/forgot-password/verify',
  AUTH_RESET_RESEND: '/api/v2/auth/forgot-password/resend',
  AUTH_RESET_PASSWORD: '/api/v2/auth/forgot-password/reset',
  AUTH_CHANGE_PASSWORD: '/api/v2/auth/change-password',
  AUTH_PROFILE_AVATAR: '/api/v2/auth/profile/avatar',

  DASHBOARD_SUMMARY: '/api/v2/dashboard/summary',

  /** Dynamic record collection: `/api/v2/records/{typeCode}` */
  RECORDS: (typeCode: string) => `/api/v2/records/${encodeURIComponent(typeCode)}`,
  RECORD_SCHEMA: (typeCode: string) => `/api/v2/records/${encodeURIComponent(typeCode)}/schema`,
  RECORD_SURFACES: '/api/v2/records/_meta/surfaces',
  RECORD_LOGS: '/api/v2/records/logs',

  // Built-in type codes (same dynamic router; kept as literals for contract checks).
  MEETING_TOPICS: '/api/v2/records/meeting_topic',
  MEETING_HISTORY: '/api/v2/records/meeting_history',
  INCOMING_DOCUMENTS: '/api/v2/records/incoming_document',
  OUTGOING_DOCUMENTS: '/api/v2/records/outgoing_document',
  DOCUMENTS: '/api/v2/records/document',
  MASTER_LIST_REQUESTS: '/api/v2/records/master_list_request',

  // Meeting board helpers under meeting_history type (no /meetings HTTP family).
  MEETINGS_REORDER: '/api/v2/records/meeting_history/reorder',
  MEETING_ASSIGN_TOPIC: (meetingId: string) =>
    `/api/v2/records/meeting_history/${encodeURIComponent(meetingId)}/assign-topic`,
  MEETING_ATTACHMENTS_LINK: (meetingId: string) =>
    `/api/v2/records/meeting_history/${encodeURIComponent(meetingId)}/attachments/link`,
  MEETING_ATTACHMENTS: (meetingId: string) =>
    `/api/v2/records/meeting_history/${encodeURIComponent(meetingId)}/attachments`,
  PORTAL_DRIVE_FILES: '/api/v2/portal/drive-files',

  /** Dynamic organization collection: `/api/v2/organizations/{orgType}` */
  ORGANIZATIONS: (orgType: string) => `/api/v2/organizations/${encodeURIComponent(orgType)}`,
  ORGANIZATION_TYPES: '/api/v2/organizations/_meta/types',
  DEPARTMENTS: '/api/v2/organizations/department',
  COMPANIES: '/api/v2/organizations/company',
  PURPOSE: '/api/v2/purpose',
  SECTOR: '/api/v2/sector',
  OFFICERS: '/api/v2/officers',

  ROLES: '/api/v2/users/roles',
  PERMISSION_CATALOG: '/api/v2/users/permission-catalog',
  USERS: '/api/v2/users',

  RECORD_TYPES: '/api/v2/configuration/record-types',
  RECORD_ATTRIBUTES: '/api/v2/configuration/record-attributes',
  CONFIGURATION_ENUMS: '/api/v2/configuration/enums',
  CONFIGURATION_ENUM_GROUP: (group: string) => `/api/v2/configuration/enums/${encodeURIComponent(group)}`,
  CONFIGURATION_ENUM_VALUE: (group: string, code: string) =>
    `/api/v2/configuration/enums/${encodeURIComponent(group)}/${encodeURIComponent(code)}`,

  APP_INFO: '/api/v2/settings/app-info',
  APP_INFO_RESET: '/api/v2/settings/app-info/reset',
  APP_CONFIG: '/api/v2/settings/app-config',
  APP_CONFIG_TEST_EMAIL: '/api/v2/settings/app-config/email/test-connection',
  APP_CONFIG_SEND_TEST_EMAIL: '/api/v2/settings/app-config/email/send-test',
  APP_CONFIG_TEST_TELEGRAM: '/api/v2/settings/app-config/telegram/test-connection',
  APP_CONFIG_SEND_TEST_TELEGRAM: '/api/v2/settings/app-config/telegram/send-test',
  STORAGE_PROVIDERS: '/api/v2/settings/storage',
  STORAGE_PROVIDER: (id: string) => `/api/v2/settings/storage/${id}`,
  STORAGE_PROVIDER_TEST: (id: string) => `/api/v2/settings/storage/${id}/test-connection`,
  STORAGE_PROVIDER_SET_DEFAULT: (id: string) => `/api/v2/settings/storage/${id}/set-default`,
  STORAGE_PROVIDER_SET_ACTIVE: (id: string) => `/api/v2/settings/storage/${id}/set-active`,

  FILE_UPLOADS: '/api/v2/portal/file-uploads',
  GOOGLE_DRIVE_SYNC: '/api/v2/portal/google-drive-sync',
  PORTAL_LOGS: '/api/v2/portal/logs',

  SYSTEM_LOGS: '/api/v2/system/logs',

  EXPORT_JOBS: '/api/v2/exports',
  SEARCH: '/api/v2/search',
  SEARCH_ASK: '/api/v2/search/ask',
  MENTIONS: '/api/v2/mentions',
  FILES: (fileId: string) => `/api/v2/files/${encodeURIComponent(fileId)}`,

  RECORD_COMMENTS: (typeCode: string, entityId: string) =>
    `/api/v2/records/${encodeURIComponent(typeCode)}/${encodeURIComponent(entityId)}/comments`,
  RECORD_ACTIVITY: (typeCode: string, entityId: string) =>
    `/api/v2/records/${encodeURIComponent(typeCode)}/${encodeURIComponent(entityId)}/activity`,
  RECORD_ATTACHMENTS: (typeCode: string, entityId: string) =>
    `/api/v2/records/${encodeURIComponent(typeCode)}/${encodeURIComponent(entityId)}/attachments`,
  /** Multipart upload + immediate attachment of real file bytes to a record/meeting. */
  RECORD_ATTACHMENT_UPLOAD: (typeCode: string, entityId: string) =>
    `/api/v2/records/${encodeURIComponent(typeCode)}/${encodeURIComponent(entityId)}/attachments/upload`,
  /** Detach a file reference from a record without deleting the shared File object. */
  RECORD_ATTACHMENT_DETACH: (typeCode: string, entityId: string, fileId: string) =>
    `/api/v2/records/${encodeURIComponent(typeCode)}/${encodeURIComponent(entityId)}/attachments/${encodeURIComponent(fileId)}`,
} as const
