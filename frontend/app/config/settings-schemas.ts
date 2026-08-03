import type { DocumentTabSchema } from '~/types/docetra/common'
import type { StorageProviderType } from '~/types/docetra/settings'

/** App Info — single tab with general / branding / footer sections. */
export const appInfoTabs: DocumentTabSchema[] = [
  {
    id: 'info',
    labelKey: 'docetra.settings.tabs.general',
    sections: [
      {
        id: 'general',
        titleKey: 'docetra.settings.generalInfo',
        descriptionKey: 'docetra.settings.generalInfoHelp',
        fields: [
          { key: 'applicationName', labelKey: 'docetra.settings.applicationName', type: 'text', required: true },
          { key: 'shortName', labelKey: 'docetra.settings.shortName', type: 'text', required: true },
          { key: 'organizationName', labelKey: 'docetra.settings.organizationName', type: 'text', colSpan: 2 },
          { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2, rows: 2 },
          { key: 'supportEmail', labelKey: 'docetra.settings.supportEmail', type: 'text' },
          { key: 'supportPhone', labelKey: 'docetra.settings.supportPhone', type: 'text' },
          { key: 'website', labelKey: 'docetra.settings.website', type: 'url' },
          { key: 'address', labelKey: 'docetra.settings.address', type: 'text' },
        ],
      },
      {
        id: 'branding',
        titleKey: 'docetra.settings.branding',
        descriptionKey: 'docetra.settings.brandingHelp',
        fields: [
          { key: 'branding.mainLogoUrl', labelKey: 'docetra.settings.mainLogo', type: 'image' },
          { key: 'branding.sidebarLogoUrl', labelKey: 'docetra.settings.sidebarLogo', type: 'image' },
          { key: 'branding.faviconUrl', labelKey: 'docetra.settings.favicon', type: 'image' },
          { key: 'branding.loginBackgroundUrl', labelKey: 'docetra.settings.loginBackground', type: 'image' },
          { key: 'branding.primaryColor', labelKey: 'docetra.settings.primaryColor', type: 'color' },
          { key: 'branding.secondaryColor', labelKey: 'docetra.settings.secondaryColor', type: 'color' },
        ],
      },
      {
        id: 'footer',
        titleKey: 'docetra.settings.footerInfo',
        fields: [
          { key: 'footer.copyrightText', labelKey: 'docetra.settings.copyright', type: 'text', colSpan: 2 },
          { key: 'footer.privacyPolicyUrl', labelKey: 'docetra.settings.privacyUrl', type: 'url', colSpan: 2 },
          { key: 'footer.termsUrl', labelKey: 'docetra.settings.termsUrl', type: 'url', colSpan: 2 },
        ],
      },
    ],
  },
]

/** App Config — 7 tabs matching the previous UI. */
export const appConfigTabs: DocumentTabSchema[] = [
  {
    id: 'general',
    labelKey: 'docetra.settings.tabs.general',
    sections: [
      {
        id: 'general',
        titleKey: 'docetra.settings.tabs.general',
        fields: [
          { key: 'general.defaultLandingPage', labelKey: 'docetra.settings.defaultLandingPage', type: 'text' },
          { key: 'general.defaultPageSize', labelKey: 'docetra.settings.defaultPageSize', type: 'number' },
          {
            key: 'general.defaultRecordView',
            labelKey: 'docetra.settings.defaultRecordView',
            type: 'select',
            options: [
              { label: 'Table', value: 'table' },
              { label: 'Kanban', value: 'kanban' },
            ],
          },
          { key: 'general.maxUploadSizeMb', labelKey: 'docetra.config.maxFileSizeMb', type: 'number' },
          { key: 'general.enableComments', labelKey: 'docetra.config.feature.comments', type: 'boolean' },
          { key: 'general.enableSharing', labelKey: 'docetra.config.feature.sharing', type: 'boolean' },
          { key: 'general.enableExport', labelKey: 'docetra.config.feature.export', type: 'boolean' },
        ],
      },
    ],
  },
  {
    id: 'localization',
    labelKey: 'docetra.settings.tabs.localization',
    sections: [
      {
        id: 'localization',
        titleKey: 'docetra.settings.tabs.localization',
        fields: [
          {
            key: 'localization.defaultLanguage',
            labelKey: 'docetra.settings.defaultLanguage',
            type: 'select',
            options: [
              { label: 'English', value: 'en' },
              { label: 'Khmer', value: 'km' },
            ],
          },
          { key: 'localization.timezone', labelKey: 'docetra.settings.timezone', type: 'text' },
          { key: 'localization.dateFormat', labelKey: 'docetra.settings.dateFormat', type: 'text' },
          { key: 'localization.timeFormat', labelKey: 'docetra.settings.timeFormat', type: 'text' },
          { key: 'localization.currency', labelKey: 'docetra.settings.currency', type: 'text' },
          { key: 'localization.locale', labelKey: 'docetra.settings.locale', type: 'text' },
        ],
      },
    ],
  },
  {
    id: 'email',
    labelKey: 'docetra.settings.tabs.email',
    sections: [
      {
        id: 'email',
        titleKey: 'docetra.settings.tabs.email',
        fields: [
          { key: 'email.enabled', labelKey: 'docetra.settings.enableEmail', type: 'boolean' },
          { key: 'email.smtpHost', labelKey: 'docetra.settings.smtpHost', type: 'text' },
          { key: 'email.smtpPort', labelKey: 'docetra.settings.smtpPort', type: 'number' },
          { key: 'email.username', labelKey: 'docetra.settings.username', type: 'text' },
          { key: 'email.password', labelKey: 'docetra.settings.password', type: 'secret' },
          {
            key: 'email.encryption',
            labelKey: 'docetra.settings.encryption',
            type: 'select',
            options: [
              { label: 'None', value: 'none' },
              { label: 'SSL', value: 'ssl' },
              { label: 'TLS', value: 'tls' },
              { label: 'STARTTLS', value: 'starttls' },
            ],
          },
          { key: 'email.fromName', labelKey: 'docetra.settings.fromName', type: 'text' },
          { key: 'email.fromEmail', labelKey: 'docetra.settings.fromEmail', type: 'text' },
          { key: 'email.replyToEmail', labelKey: 'docetra.settings.replyTo', type: 'text' },
          { key: '__emailConnection', labelKey: 'docetra.connection.title', type: 'connection-status', colSpan: 2 },
        ],
      },
    ],
  },
  {
    id: 'telegram',
    labelKey: 'docetra.settings.tabs.telegram',
    sections: [
      {
        id: 'telegram',
        titleKey: 'docetra.settings.tabs.telegram',
        fields: [
          { key: 'telegram.enabled', labelKey: 'docetra.settings.enableTelegram', type: 'boolean' },
          { key: 'telegram.botDisplayName', labelKey: 'docetra.settings.botDisplayName', type: 'text' },
          { key: 'telegram.botToken', labelKey: 'docetra.settings.botToken', type: 'secret' },
          { key: 'telegram.botUsername', labelKey: 'docetra.settings.botUsername', type: 'text' },
          {
            key: 'telegram.messageLanguage',
            labelKey: 'docetra.settings.messageLanguage',
            type: 'select',
            options: [
              { label: 'English', value: 'en' },
              { label: 'Khmer', value: 'km' },
            ],
          },
          { key: 'telegram.includeRecordLink', labelKey: 'docetra.settings.includeRecordLink', type: 'boolean' },
          { key: 'telegram.includeOrganization', labelKey: 'docetra.settings.includeOrganization', type: 'boolean' },
          { key: 'telegram.includeAssignedOfficer', labelKey: 'docetra.settings.includeAssignedOfficer', type: 'boolean' },
          {
            key: 'telegram.messageTemplate',
            labelKey: 'docetra.settings.messageTemplate',
            type: 'textarea',
            colSpan: 2,
            rows: 6,
          },
          {
            key: 'telegram.destinations',
            labelKey: 'docetra.settings.destinations',
            type: 'telegram-destinations',
            colSpan: 2,
          },
          { key: '__telegramConnection', labelKey: 'docetra.connection.title', type: 'connection-status', colSpan: 2 },
        ],
      },
    ],
  },
  {
    id: 'notifications',
    labelKey: 'docetra.settings.tabs.notifications',
    sections: [
      {
        id: 'notifications',
        titleKey: 'docetra.settings.tabs.notifications',
        fields: [
          { key: 'notifications.inAppEnabled', labelKey: 'docetra.settings.inApp', type: 'boolean' },
          { key: 'notifications.emailEnabled', labelKey: 'docetra.settings.emailChannel', type: 'boolean' },
          { key: 'notifications.telegramEnabled', labelKey: 'docetra.settings.telegramChannel', type: 'boolean' },
          { key: 'notifications.deliveryRetries', labelKey: 'docetra.settings.deliveryRetries', type: 'number' },
          {
            key: 'notifications.rules',
            labelKey: 'docetra.settings.eventRules',
            type: 'notification-rules',
            colSpan: 2,
          },
        ],
      },
    ],
  },
  {
    id: 'security',
    labelKey: 'docetra.settings.tabs.security',
    sections: [
      {
        id: 'security',
        titleKey: 'docetra.settings.tabs.security',
        fields: [
          {
            key: '__securityAlert',
            labelKey: 'docetra.settings.securityDisclaimer',
            type: 'alert',
            helpKey: 'docetra.settings.securityDisclaimerHelp',
            alertColor: 'warning',
            colSpan: 2,
          },
          { key: 'security.sessionTimeoutMinutes', labelKey: 'docetra.settings.sessionTimeout', type: 'number' },
          { key: 'security.maxLoginAttempts', labelKey: 'docetra.settings.maxLoginAttempts', type: 'number' },
          { key: 'security.accountLockMinutes', labelKey: 'docetra.settings.accountLockMinutes', type: 'number' },
          { key: 'security.passwordExpiryDays', labelKey: 'docetra.settings.passwordExpiryDays', type: 'number' },
          { key: 'security.auditRetentionDays', labelKey: 'docetra.settings.auditRetentionDays', type: 'number' },
          { key: 'security.requirePasswordChange', labelKey: 'docetra.settings.requirePasswordChange', type: 'boolean' },
          {
            key: 'security.allowedUploadExtensions',
            labelKey: 'docetra.config.allowedExtensions',
            type: 'csv-list',
            colSpan: 2,
          },
        ],
      },
    ],
  },
  {
    id: 'system',
    labelKey: 'docetra.settings.tabs.system',
    sections: [
      {
        id: 'system',
        titleKey: 'docetra.settings.tabs.system',
        fields: [
          { key: 'system.maintenanceMode', labelKey: 'docetra.settings.maintenanceMode', type: 'boolean' },
          { key: 'system.readOnlyMode', labelKey: 'docetra.settings.readOnlyMode', type: 'boolean' },
          { key: 'system.paginationDefault', labelKey: 'docetra.settings.paginationDefault', type: 'number' },
          { key: 'system.configurationVersion', labelKey: 'docetra.settings.configurationVersion', type: 'text', readOnly: true },
          { key: 'system.environment', labelKey: 'docetra.settings.environment', type: 'text', readOnly: true },
          { key: 'system.cacheStatus', labelKey: 'docetra.settings.cacheStatus', type: 'text', readOnly: true },
          { key: 'system.backgroundJobStatus', labelKey: 'docetra.settings.jobStatus', type: 'text', readOnly: true },
        ],
      },
    ],
  },
]

const storageBaseFields = [
  { key: 'name', labelKey: 'docetra.fields.name', type: 'text' as const, required: true },
  { key: 'type', labelKey: 'docetra.settings.providerType', type: 'text' as const, readOnly: true },
  { key: 'maxFileSizeMb', labelKey: 'docetra.config.maxFileSizeMb', type: 'number' as const },
  { key: 'allowedFileTypes', labelKey: 'docetra.config.allowedExtensions', type: 'csv-list' as const },
  { key: 'uploadPathPattern', labelKey: 'docetra.settings.uploadPathPattern', type: 'text' as const, colSpan: 2 as const },
  { key: 'active', labelKey: 'docetra.status.active', type: 'boolean' as const },
  {
    key: 'accessMode',
    labelKey: 'docetra.settings.accessMode',
    type: 'select' as const,
    options: [
      { label: 'Private', value: 'private' },
      { label: 'Public', value: 'public' },
    ],
  },
]

const storageS3Fields = [
  { key: 'endpoint', labelKey: 'docetra.settings.endpoint', type: 'text' as const },
  { key: 'region', labelKey: 'docetra.settings.region', type: 'text' as const },
  { key: 'bucket', labelKey: 'docetra.settings.bucket', type: 'text' as const },
  { key: 'publicUrl', labelKey: 'docetra.settings.publicUrl', type: 'url' as const },
  { key: 'accessKey', labelKey: 'docetra.settings.accessKey', type: 'text' as const },
  { key: 'secretKey', labelKey: 'docetra.settings.secretKey', type: 'secret' as const },
  { key: 'pathStyle', labelKey: 'docetra.settings.pathStyle', type: 'boolean' as const },
]

const storageDriveFields = [
  { key: 'folderId', labelKey: 'docetra.settings.folderId', type: 'text' as const },
  { key: 'syncSchedule', labelKey: 'docetra.settings.syncSchedule', type: 'text' as const },
]

/** Storage provider editor form — sections depend on provider type. */
export function storageProviderTabs(type: StorageProviderType | null | undefined): DocumentTabSchema[] {
  const sections: DocumentTabSchema['sections'] = [
    {
      id: 'basics',
      titleKey: 'docetra.settings.tabs.general',
      fields: [...storageBaseFields],
    },
  ]

  if (type && ['cloudflare_r2', 'amazon_s3', 'minio'].includes(type)) {
    sections.push({
      id: 's3',
      titleKey: 'docetra.settings.s3Settings',
      fields: [...storageS3Fields],
    })
  }

  if (type === 'google_drive') {
    sections.push({
      id: 'drive',
      titleKey: 'docetra.settings.driveSettings',
      fields: [...storageDriveFields],
    })
  }

  sections.push({
    id: 'connection',
    titleKey: 'docetra.connection.title',
    fields: [
      { key: '__storageConnection', labelKey: 'docetra.connection.title', type: 'connection-status', colSpan: 2 },
    ],
  })

  return [
    {
      id: 'provider',
      labelKey: 'docetra.pages.storage',
      sections,
    },
  ]
}
