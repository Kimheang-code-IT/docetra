import type { DocumentTabSchema } from '~/types/docetra/common'
import {
  AWS_REGION_OPTIONS,
  DATE_FORMAT_OPTIONS,
  SYNC_SCHEDULE_OPTIONS,
  TIME_FORMAT_OPTIONS,
  TIMEZONE_OPTIONS,
} from '~/utils/constants/select-options'

/** App Config — tabs for the runtime configuration. */
export const appConfigTabs: DocumentTabSchema[] = [
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
          {
            key: 'localization.timezone',
            labelKey: 'docetra.settings.timezone',
            type: 'select',
            options: TIMEZONE_OPTIONS,
          },
          {
            key: 'localization.dateFormat',
            labelKey: 'docetra.settings.dateFormat',
            type: 'select',
            options: DATE_FORMAT_OPTIONS,
          },
          {
            key: 'localization.timeFormat',
            labelKey: 'docetra.settings.timeFormat',
            type: 'select',
            options: TIME_FORMAT_OPTIONS,
          },
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
          { key: 'telegram.botToken', labelKey: 'docetra.settings.botToken', type: 'secret' },
          {
            key: 'telegram.messageLanguage',
            labelKey: 'docetra.settings.messageLanguage',
            type: 'select',
            options: [
              { label: 'English', value: 'en' },
              { label: 'Khmer', value: 'km' },
            ],
          },
          { key: 'telegram.includeOrganization', labelKey: 'docetra.settings.includeOrganization', type: 'boolean' },
          {
            key: 'telegram.destinations',
            labelKey: 'docetra.settings.destinations',
            type: 'telegram-destinations',
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
          { key: 'security.sessionTimeoutMinutes', labelKey: 'docetra.settings.sessionTimeout', type: 'number' },
          { key: 'security.maxLoginAttempts', labelKey: 'docetra.settings.maxLoginAttempts', type: 'number' },
          { key: 'security.accountLockMinutes', labelKey: 'docetra.settings.accountLockMinutes', type: 'number' },
          { key: 'security.passwordExpiryDays', labelKey: 'docetra.settings.passwordExpiryDays', type: 'number' },
          { key: 'security.auditRetentionDays', labelKey: 'docetra.settings.auditRetentionDays', type: 'number' },
          { key: 'security.requirePasswordChange', labelKey: 'docetra.settings.requirePasswordChange', type: 'boolean' },
        ],
      },
    ],
  },
]

const storageConnectionField = {
  key: '__storageConnection',
  labelKey: 'docetra.connection.title',
  type: 'connection-status' as const,
  colSpan: 2 as const,
}

/** Storage settings — S3 and Google Drive only. */
export const storageSettingsTabs: DocumentTabSchema[] = [
  {
    id: 'amazon_s3',
    labelKey: 'docetra.settings.storageTabs.amazonS3',
    sections: [
      {
        id: 's3-connection',
        titleKey: 'docetra.settings.connectionSettings',
        fields: [
          {
            key: 'region',
            labelKey: 'docetra.settings.region',
            type: 'select',
            required: true,
            options: AWS_REGION_OPTIONS,
          },
          { key: 'bucket', labelKey: 'docetra.settings.bucket', type: 'text', required: true },
          { key: 'endpoint', labelKey: 'docetra.settings.endpoint', type: 'text', colSpan: 2 },
          { key: 'publicUrl', labelKey: 'docetra.settings.publicUrl', type: 'url', colSpan: 2 },
          { key: 'accessKey', labelKey: 'docetra.settings.accessKey', type: 'text', required: true },
          { key: 'secretKey', labelKey: 'docetra.settings.secretKey', type: 'secret', required: true },
        ],
      },
      {
        id: 's3-status',
        titleKey: 'docetra.connection.title',
        fields: [storageConnectionField],
      },
    ],
  },
  {
    id: 'google_drive',
    labelKey: 'docetra.settings.storageTabs.googleDrive',
    sections: [
      {
        id: 'drive-connection',
        titleKey: 'docetra.settings.connectionSettings',
        fields: [
          { key: 'clientId', labelKey: 'docetra.settings.clientId', type: 'text', required: true, colSpan: 2 },
          { key: 'clientSecret', labelKey: 'docetra.settings.clientSecret', type: 'secret', required: true, colSpan: 2 },
          { key: 'folderId', labelKey: 'docetra.settings.folderId', type: 'text', required: true },
          {
            key: 'syncSchedule',
            labelKey: 'docetra.settings.syncSchedule',
            type: 'select',
            options: SYNC_SCHEDULE_OPTIONS,
          },
        ],
      },
      {
        id: 'drive-status',
        titleKey: 'docetra.connection.title',
        fields: [storageConnectionField],
      },
    ],
  },
]

