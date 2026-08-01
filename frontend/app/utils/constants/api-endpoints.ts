export const ApiEndpoints = {
  AUTH_LOGIN: '/api/v2/auth/login',
  AUTH_FORGOT_PASSWORD: '/api/v2/auth/forgot-password',
  AUTH_RESET_VERIFY: '/api/v2/auth/forgot-password/verify',
  AUTH_RESET_RESEND: '/api/v2/auth/forgot-password/resend',

  DASHBOARD_SUMMARY: '/api/v2/dashboard/summary',

  MEETING_TOPICS: '/api/v2/meetings/topics',
  MEETING_HISTORY: '/api/v2/meetings/history',

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
  USERS: '/api/v2/users',

  RECORD_TYPES: '/api/v2/configuration/record-types',
  RECORD_ATTRIBUTES: '/api/v2/configuration/record-attributes',
  DOCUMENT_TYPES: '/api/v2/configuration/document-types',

  FILE_UPLOADS: '/api/v2/portal/file-uploads',
  GOOGLE_DRIVE_SYNC: '/api/v2/portal/google-drive-sync',
  PORTAL_LOGS: '/api/v2/portal/logs',

  SYSTEM_LOGS: '/api/v2/system/logs',

  COMMENTS: (entityType: string, entityId: string) =>
    `/api/v2/${entityType}/${entityId}/comments`,
  ACTIVITY: (entityType: string, entityId: string) =>
    `/api/v2/${entityType}/${entityId}/activity`,
  ATTACHMENTS: (entityType: string, entityId: string) =>
    `/api/v2/${entityType}/${entityId}/attachments`,
} as const
