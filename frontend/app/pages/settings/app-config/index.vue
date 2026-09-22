<script setup lang="ts">
import type { AppConfig, CreateStorageProviderInput, StorageProvider, StorageProviderType } from '~/types/docetra/settings'
import type { ConnectionStatusFieldValue } from '~/types/docetra/common'
import { appConfigTabs, storageSettingsTabs } from '~/config/settings-schemas'
import { useSettingsRepositories } from '~/repositories'
import { useConfirm } from '~/composables/common/useConfirm'
import { useAppPageTitle } from '~/composables/layout/useAppPageTitle'
import { usePathModel } from '~/composables/common/usePathModel'
import { getByPath, setByPath } from '~/utils/object-path'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

definePageMeta({
  titleKey: 'docetra.pages.appConfig',
  permission: 'settings.app_config.view',
})

const STORAGE_TAB_TYPES = storageSettingsTabs.map(tab => tab.id) as StorageProviderType[]
const activeTab = ref('localization')
const tabs = computed(() => [...appConfigTabs, ...storageSettingsTabs])
const onStorageTab = computed(() => STORAGE_TAB_TYPES.includes(activeTab.value as StorageProviderType))

const { appConfig, storage } = useSettingsRepositories()
const { t } = useI18n()
const toast = useToast()
const { confirm } = useConfirm()
const auth = useAuthStore()
const appLocalization = useAppLocalization()

const canEditApp = computed(() => auth.canAccessPage('settings.app_config.edit'))
const canConfigureApp = computed(() => auth.canAccessPage('settings.app_config.configure'))
const canEditStorage = computed(() => auth.canAccessPage('settings.storage.edit'))
const canConfigureStorage = computed(() => auth.canAccessPage('settings.storage.configure'))
const canEdit = computed(() => (onStorageTab.value ? canEditStorage.value : canEditApp.value))
const canConfigure = computed(() => (onStorageTab.value ? canConfigureStorage.value : canConfigureApp.value))

const pending = ref(true)
const saving = ref(false)
const testingEmail = ref(false)
const testingTelegram = ref(false)
const testingStorage = ref(false)
const creatingStorage = ref(false)
const model = ref<AppConfig | null>(null)

const providers = ref<StorageProvider[]>([])
const providersLoaded = ref(false)
const draft = ref<StorageProvider | null>(null)
const pathModel = usePathModel(draft)

const pagePending = computed(() => (onStorageTab.value ? !providersLoaded.value : pending.value || !model.value))

async function load() {
  pending.value = true
  try {
    model.value = await appConfig.get()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
  }
  finally {
    pending.value = false
  }
}

function providerForTab(type: string) {
  return providers.value.find(provider => provider.type === type) || null
}

/** Clone without structuredClone — works with Vue reactive proxies. */
function cloneProvider(value: StorageProvider): StorageProvider {
  return JSON.parse(JSON.stringify(value)) as StorageProvider
}

function applyDraftForTab(type: string) {
  const found = providerForTab(type)
  draft.value = found ? cloneProvider(found) : null
}

async function loadStorageProviders() {
  providersLoaded.value = false
  try {
    const all = await storage.list()
    providers.value = all.filter(provider => STORAGE_TAB_TYPES.includes(provider.type))
    applyDraftForTab(activeTab.value)
  }
  catch (e: any) {
    providers.value = []
    draft.value = null
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
  }
  finally {
    providersLoaded.value = true
  }
}

watch(activeTab, async (tab) => {
  if (!STORAGE_TAB_TYPES.includes(tab as StorageProviderType)) return
  if (!providersLoaded.value) await loadStorageProviders()
  else applyDraftForTab(tab)
})

function storageConnectionValue(provider: StorageProvider): ConnectionStatusFieldValue {
  return {
    status: provider.connectionStatus,
    message: provider.lastTestMessage,
    lastTestedAt: provider.lastTestedAt,
    details: [
      { label: t('docetra.settings.providerType'), value: provider.type.replaceAll('_', ' ') },
      { label: t('docetra.settings.default'), value: provider.isDefault ? t('docetra.common.yes') : t('docetra.common.no') },
    ],
  }
}

function fieldValue(key: string): unknown {
  if (onStorageTab.value) {
    if (!draft.value) return undefined
    if (key === '__storageConnection') return storageConnectionValue(draft.value)
    return pathModel.fieldValue(key)
  }

  if (!model.value) return undefined

  return getByPath(model.value, key)
}

function setFieldValue(key: string, value: unknown) {
  if (onStorageTab.value) {
    if (!draft.value) return
    if (key === '__storageConnection') return
    pathModel.setFieldValue(key, value)
    return
  }

  if (!model.value) return

  setByPath(model.value as any, key, value)
}

async function save() {
  if (onStorageTab.value) {
    if (!draft.value) return
    saving.value = true
    try {
      await storage.update(draft.value.id, draft.value)
      toast.add({ title: t('docetra.common.saved'), color: 'success' })
      await loadStorageProviders()
    }
    catch (e: any) {
      toast.add({ title: e?.message || t('docetra.common.saveFailed'), color: 'error' })
    }
    finally {
      saving.value = false
    }
    return
  }

  if (!model.value) return
  saving.value = true
  try {
    model.value = await appConfig.update(model.value)
    appLocalization.apply(model.value.localization)
    const { useAppRuntimeConfig } = await import('~/composables/settings/useAppRuntimeConfig')
    useAppRuntimeConfig().applyFromConfig(model.value)
    usePreferencesStore().syncLocaleWithConfig()
    const { invalidateCardFieldsCache } = await import('~/composables/settings/useCardFields')
    invalidateCardFieldsCache()
    toast.add({ title: t('docetra.common.saved'), color: 'success' })
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.saveFailed'), color: 'error' })
  }
  finally {
    saving.value = false
  }
}

function storageTabLabelKey(type: StorageProviderType) {
  if (type === 'amazon_s3') return 'docetra.settings.storageTabs.amazonS3'
  if (type === 'google_drive') return 'docetra.settings.storageTabs.googleDrive'
  return `docetra.settings.storageTabs.${type}`
}

async function createStorageProvider() {
  if (creatingStorage.value) return
  const type = activeTab.value as StorageProviderType
  creatingStorage.value = true
  try {
    await storage.create({
      name: t(storageTabLabelKey(type)),
      type,
      active: false,
    } as CreateStorageProviderInput)
    toast.add({ title: t('docetra.settings.providerCreated'), color: 'success' })
    await loadStorageProviders()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
  finally {
    creatingStorage.value = false
  }
}

async function testStorage() {
  if (!draft.value) return
  testingStorage.value = true
  try {
    // Persist the draft first so the backend tests the current form values.
    await storage.update(draft.value.id, draft.value)
    const result = await storage.testConnection(draft.value.id)
    toast.add({
      title: result.message,
      color: result.status === 'connected' ? 'success' : 'error',
    })
    await loadStorageProviders()
  }
  finally {
    testingStorage.value = false
  }
}

async function toggleStorageActive() {
  if (!draft.value) return
  saving.value = true
  try {
    await storage.setActive(draft.value.id, !draft.value.active)
    toast.add({
      title: draft.value.active ? t('docetra.settings.deactivated') : t('docetra.settings.activated'),
      color: 'success',
    })
    await loadStorageProviders()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
  finally {
    saving.value = false
  }
}

async function setStorageDefault() {
  if (!draft.value) return
  try {
    await storage.setDefault(draft.value.id)
    toast.add({ title: t('docetra.settings.defaultUpdated'), color: 'success' })
    await loadStorageProviders()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
}

async function removeStorageProvider() {
  if (!draft.value || draft.value.isDefault) return
  const ok = await confirm({ kind: 'delete' })
  if (!ok) return
  saving.value = true
  try {
    await storage.remove(draft.value.id)
    toast.add({ title: t('docetra.settings.providerDeleted'), color: 'success' })
    draft.value = null
    await loadStorageProviders()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
  finally {
    saving.value = false
  }
}

async function testEmail() {
  testingEmail.value = true
  try {
    if (model.value) await appConfig.update({ email: model.value.email })
    const result = await appConfig.testEmailConnection()
    model.value = await appConfig.get()
    toast.add({
      title: result.message,
      color: result.status === 'connected' ? 'success' : 'error',
    })
  }
  finally {
    testingEmail.value = false
  }
}

async function testTelegram() {
  testingTelegram.value = true
  try {
    if (model.value) await appConfig.update({ telegram: model.value.telegram })
    const result = await appConfig.testTelegramConnection()
    model.value = await appConfig.get()
    toast.add({
      title: result.message,
      color: result.status === 'connected' ? 'success' : 'error',
    })
  }
  finally {
    testingTelegram.value = false
  }
}

onMounted(() => void load())
useAppPageTitle(() => t('docetra.pages.appConfig'))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="tabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pagePending"
    :saving="saving"
    :read-only="!canEdit"
    :can-save="canEdit"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="false"
    @save="save"
    @refresh="onStorageTab ? loadStorageProviders : load"
  >
    <template #actions>
      <CommonAppConnectionTestButton
        v-if="activeTab === 'email' && canConfigure"
        :loading="testingEmail"
        @click="testEmail"
      />
      <CommonAppConnectionTestButton
        v-if="activeTab === 'telegram' && canConfigure"
        :loading="testingTelegram"
        @click="testTelegram"
      />

      <UButton
        v-if="onStorageTab && !draft && canConfigure"
        size="sm"
        icon="i-lucide-plus"
        :loading="creatingStorage"
        :disabled="creatingStorage"
        @click="createStorageProvider"
      >
        {{ t('docetra.settings.createProvider') }}
      </UButton>
      <CommonAppConnectionTestButton
        v-if="onStorageTab && draft && canConfigure"
        :loading="testingStorage"
        @click="testStorage"
      />
      <UButton
        v-if="onStorageTab && draft && canConfigure"
        color="neutral"
        variant="soft"
        :icon="draft.active ? 'i-lucide-toggle-right' : 'i-lucide-toggle-left'"
        @click="toggleStorageActive"
      >
        {{ draft.active ? t('docetra.settings.deactivate') : t('docetra.settings.activate') }}
      </UButton>
      <UButton
        v-if="onStorageTab && draft && !draft.isDefault && canConfigure"
        color="neutral"
        variant="soft"
        icon="i-lucide-star"
        @click="setStorageDefault"
      >
        {{ t('docetra.settings.setDefault') }}
      </UButton>
      <UButton
        v-if="onStorageTab && draft && !draft.isDefault && canConfigure"
        color="error"
        variant="soft"
        icon="i-lucide-trash-2"
        @click="removeStorageProvider"
      >
        {{ t('actions.delete') }}
      </UButton>
      <UBadge
        v-else-if="onStorageTab && draft?.isDefault"
        color="primary"
        variant="subtle"
        class="self-center"
      >
        {{ t('docetra.settings.default') }}
      </UBadge>
    </template>
  </DocumentAppDocumentPage>
</template>
