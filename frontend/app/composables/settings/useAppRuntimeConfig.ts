import type { AppConfigGeneral, AppConfigSecurity } from '~/types/docetra/settings'
import { useSettingsRepositories } from '~/repositories'
import { extensionsToUppyTypes } from '~/utils/security/files'

const DEFAULT_GENERAL: AppConfigGeneral = {
  defaultLandingPage: '/',
  defaultPageSize: 20,
  defaultRecordView: 'table',
  enableComments: true,
  enableSharing: true,
  enableExport: true,
  maxUploadSizeMb: 25,
}

const DEFAULT_SECURITY: AppConfigSecurity = {
  sessionTimeoutMinutes: 480,
  maxLoginAttempts: 5,
  accountLockMinutes: 15,
  passwordExpiryDays: 0,
  requirePasswordChange: false,
  allowedUploadExtensions: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'],
  auditRetentionDays: 365,
  frontendOnly: false,
}

/** App Config general + security for runtime UI (page size, uploads). */
export function useAppRuntimeConfig() {
  const general = useState<AppConfigGeneral>('app-runtime-general', () => ({ ...DEFAULT_GENERAL }))
  const security = useState<AppConfigSecurity>('app-runtime-security', () => ({ ...DEFAULT_SECURITY }))
  const loaded = useState('app-runtime-config-loaded', () => false)
  const loading = useState('app-runtime-config-loading', () => false)

  async function load(force = false) {
    if (loaded.value && !force) return
    if (loading.value && !force) {
      await until(loading).toBe(false)
      return
    }
    loading.value = true
    try {
      const config = await useSettingsRepositories().appConfig.get()
      general.value = { ...DEFAULT_GENERAL, ...(config.general || {}) }
      security.value = {
        ...DEFAULT_SECURITY,
        ...(config.security || {}),
        frontendOnly: false,
        allowedUploadExtensions: config.security?.allowedUploadExtensions?.length
          ? [...config.security.allowedUploadExtensions]
          : [...DEFAULT_SECURITY.allowedUploadExtensions],
      }
      loaded.value = true
    }
    catch {
      loaded.value = true
    }
    finally {
      loading.value = false
    }
  }

  function applyFromConfig(config: { general?: Partial<AppConfigGeneral>, security?: Partial<AppConfigSecurity> }) {
    if (config.general) general.value = { ...general.value, ...config.general }
    if (config.security) {
      security.value = {
        ...security.value,
        ...config.security,
        frontendOnly: false,
        allowedUploadExtensions: config.security.allowedUploadExtensions?.length
          ? [...config.security.allowedUploadExtensions]
          : security.value.allowedUploadExtensions,
      }
    }
    loaded.value = true
  }

  const defaultPageSize = computed(() => {
    const fromGeneral = Number(general.value.defaultPageSize)
    return Number.isFinite(fromGeneral) && fromGeneral > 0 ? fromGeneral : 20
  })

  const maxUploadSizeMb = computed(() => {
    const fromGeneral = Number(general.value.maxUploadSizeMb)
    return Number.isFinite(fromGeneral) && fromGeneral > 0 ? fromGeneral : 25
  })

  const allowedUploadTypes = computed(() => extensionsToUppyTypes(security.value.allowedUploadExtensions || []))

  onMounted(() => { void load() })

  return {
    general: readonly(general),
    security: readonly(security),
    loaded: readonly(loaded),
    loading: readonly(loading),
    defaultPageSize,
    maxUploadSizeMb,
    allowedUploadTypes,
    load,
    applyFromConfig,
  }
}
