export const ApiEndpoints = {
  AUTH_LOGIN: '/api/v2/auth/login',
  AUTH_LOGOUT: '/api/v2/auth/logout',
  AUTH_ME: '/api/v2/auth/me',
  AUTH_FORGOT_PASSWORD: '/api/v2/auth/forgot-password',
  AUTH_RESET_VERIFY: '/api/v2/auth/forgot-password/verify',
  AUTH_RESET_RESEND: '/api/v2/auth/forgot-password/resend',
  AUTH_RESET_PASSWORD: '/api/v2/auth/forgot-password/reset',
  AUTH_CHANGE_PASSWORD: '/api/v2/auth/change-password',
  AUTH_PROFILE_AVATAR: '/api/v2/auth/profile/avatar',

  DASHBOARD_SUMMARY: '/api/v2/dashboard/summary',

  MEETING_TOPICS: '/api/v2/meetings/topics',
  MEETING_HISTORY: '/api/v2/meetings/history',
  MEETINGS_REORDER: '/api/v2/meetings/reorder',
  MEETING_ASSIGN_TOPIC: (meetingId: string) =>
    `/api/v2/meetings/history/${encodeURIComponent(meetingId)}/assign-topic`,
  MEETING_ATTACHMENTS_LINK: (meetingId: string) =>
    `/api/v2/meetings/history/${encodeURIComponent(meetingId)}/attachments/link`,
  MEETING_ATTACHMENTS: (meetingId: string) =>
    `/api/v2/meetings/history/${encodeURIComponent(meetingId)}/attachments`,
  PORTAL_DRIVE_FILES: '/api/v2/portal/drive-files',

  INCOMING_DOCUMENTS: '/api/v2/records/incoming-documents',
  OUTGOING_DOCUMENTS: '/api/v2/records/outgoing-documents',
  DOCUMENTS: '/api/v2/records/documents',
  MASTER_LIST_REQUESTS: '/api/v2/records/master-list-requests',
  RECORD_LOGS: '/api/v2/records/logs',

  DEPARTMENTS: '/api/v2/organizations/departments',
  COMPANIES: '/api/v2/organizations/companies',
  COMPANY_PURPOSES: '/api/v2/organizations/company-purposes',
  COMPANY_SECTORS: '/api/v2/organizations/company-sectors',
  OFFICERS: '/api/v2/organizations/officers',

  ROLES: '/api/v2/users/roles',
  PERMISSION_CATALOG: '/api/v2/users/permission-catalog',
  USERS: '/api/v2/users',

  RECORD_TYPES: '/api/v2/configuration/record-types',
  RECORD_ATTRIBUTES: '/api/v2/configuration/record-attributes',

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

  COMMENTS: (entityType: string, entityId: string) =>
    `/api/v2/${entityType}/${entityId}/comments`,
  ACTIVITY: (entityType: string, entityId: string) =>
    `/api/v2/${entityType}/${entityId}/activity`,
  ATTACHMENTS: (entityType: string, entityId: string) =>
    `/api/v2/${entityType}/${entityId}/attachments`,
} as const
