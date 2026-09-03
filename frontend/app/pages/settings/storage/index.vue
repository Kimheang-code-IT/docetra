<script setup lang="ts">
import type { CreateStorageProviderInput, StorageProvider, StorageProviderType } from '~/types/docetra/settings'
import type { ConnectionStatusFieldValue } from '~/types/docetra/common'
import { storageSettingsTabs } from '~/config/settings-schemas'
import { useSettingsRepositories } from '~/repositories'
import { usePathModel } from '~/composables/common/usePathModel'
import { useConfirm } from '~/composables/common/useConfirm'
import { useAppPageTitle } from '~/composables/layout/useAppPageTitle'

definePageMeta({
  titleKey: 'docetra.pages.storage',
  permission: 'settings.storage.view',
})

const STORAGE_TAB_TYPES = storageSettingsTabs.map(tab => tab.id) as StorageProviderType[]

const { storage } = useSettingsRepositories()
const { t } = useI18n()
const toast = useToast()
const auth = useAuthStore()
const canEdit = computed(() => auth.canAccessPage('settings.storage.edit'))
const canConfigure = computed(() => auth.canAccessPage('settings.storage.configure'))

const pending = ref(true)
const saving = ref(false)
const testing = ref(false)
const creating = ref(false)
const { confirm } = useConfirm()
const providers = ref<StorageProvider[]>([])
const draft = ref<StorageProvider | null>(null)
const pathModel = usePathModel(draft)
const activeTab = ref<string>(STORAGE_TAB_TYPES[0] || 'amazon_s3')

const tabs = storageSettingsTabs

function providerForTab(type: string) {
  return providers.value.find(p => p.type === type) || null
}

/** Clone without structuredClone — works with Vue reactive proxies. */
function cloneProvider(value: StorageProvider): StorageProvider {
  return JSON.parse(JSON.stringify(value)) as StorageProvider
}

function applyDraftForTab(type: string) {
  const found = providerForTab(type)
  draft.value = found ? cloneProvider(found) : null
}

async function load() {
  pending.value = true
  try {
    const all = await storage.list()
    // Only keep providers that have a settings tab (S3, Google Drive).
    providers.value = all.filter(p => STORAGE_TAB_TYPES.includes(p.type))
    if (!providerForTab(activeTab.value) && providers.value[0]) {
      activeTab.value = providers.value[0].type
    }
    applyDraftForTab(activeTab.value)
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
    draft.value = null
  }
  finally {
    pending.value = false
  }
}

watch(activeTab, (type) => {
  // Avoid clearing draft while the initial load is still in flight.
  if (pending.value) return
  applyDraftForTab(type)
})

function fieldValue(key: string): unknown {
  if (!draft.value) return undefined

  if (key === '__storageConnection') {
    const value: ConnectionStatusFieldValue = {
      status: draft.value.connectionStatus,
      message: draft.value.lastTestMessage,
      lastTestedAt: draft.value.lastTestedAt,
      details: [
        { label: t('docetra.settings.providerType'), value: draft.value.type.replaceAll('_', ' ') },
        {
          label: t('docetra.settings.default'),
          value: draft.value.isDefault ? t('docetra.common.yes') : t('docetra.common.no'),
        },
      ],
    }
    return value
  }

  return pathModel.fieldValue(key)
}

function setFieldValue(key: string, value: unknown) {
  if (!draft.value) return
  if (key === '__storageConnection' || key === 'type') return
  pathModel.setFieldValue(key, value)
}

async function save() {
  if (!draft.value) return
  saving.value = true
  try {
    await storage.update(draft.value.id, draft.value)
    toast.add({ title: t('docetra.common.saved'), color: 'success' })
    await load()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.saveFailed'), color: 'error' })
  }
  finally {
    saving.value = false
  }
}

async function setDefault() {
  if (!draft.value) return
  try {
    await storage.setDefault(draft.value.id)
    toast.add({ title: t('docetra.settings.defaultUpdated'), color: 'success' })
    await load()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
}

async function createProvider() {
  if (creating.value) return
  const type = activeTab.value as StorageProviderType
  creating.value = true
  try {
    await storage.create({
      name: t(`docetra.settings.storageTabs.${type === 'minio' ? 'minio' : type}`),
      type,
      active: false,
    } as CreateStorageProviderInput)
    toast.add({ title: t('docetra.settings.providerCreated'), color: 'success' })
    await load()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
  finally {
    creating.value = false
  }
}

async function toggleActive() {
  if (!draft.value) return
  saving.value = true
  try {
    await storage.setActive(draft.value.id, !draft.value.active)
    toast.add({
      title: draft.value.active ? t('docetra.settings.deactivated') : t('docetra.settings.activated'),
      color: 'success',
    })
    await load()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
  finally {
    saving.value = false
  }
}

async function removeProvider() {
  if (!draft.value || draft.value.isDefault) return
  const ok = await confirm({ kind: 'delete' })
  if (!ok) return
  saving.value = true
  try {
    await storage.remove(draft.value.id)
    toast.add({ title: t('docetra.settings.providerDeleted'), color: 'success' })
    draft.value = null
    await load()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
  finally {
    saving.value = false
  }
}

async function testConnection() {
  if (!draft.value) return
  testing.value = true
  try {
    // Persist the draft first so the backend tests the current form values.
    await storage.update(draft.value.id, draft.value)
    const result = await storage.testConnection(draft.value.id)
    toast.add({
      title: result.message,
      color: result.status === 'connected' ? 'success' : 'error',
    })
    await load()
  }
  finally {
    testing.value = false
  }
}

onMounted(() => void load())
useAppPageTitle(() => t('docetra.pages.storage'))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="tabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending"
    :saving="saving"
    :read-only="!canEdit"
    :can-save="Boolean(draft) && canEdit"
    :error="!pending && !draft ? t('docetra.common.loadFailed') : null"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="false"
    content-wide
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <UButton
        v-if="!draft && canConfigure"
        size="sm"
        icon="i-lucide-plus"
        :loading="creating"
        :disabled="creating"
        @click="createProvider"
      >
        {{ t('docetra.settings.createProvider') }}
      </UButton>
      <CommonAppConnectionTestButton
        v-if="draft && canConfigure"
        :loading="testing"
        @click="testConnection"
      />
      <UButton
        v-if="draft && canConfigure"
        color="neutral"
        variant="soft"
        :icon="draft.active ? 'i-lucide-toggle-right' : 'i-lucide-toggle-left'"
        @click="toggleActive"
      >
        {{ draft.active ? t('docetra.settings.deactivate') : t('docetra.settings.activate') }}
      </UButton>
      <UButton
        v-if="draft && !draft.isDefault && canConfigure"
        color="neutral"
        variant="soft"
        icon="i-lucide-star"
        @click="setDefault"
      >
        {{ t('docetra.settings.setDefault') }}
      </UButton>
      <UButton
        v-if="draft && !draft.isDefault && canConfigure"
        color="error"
        variant="soft"
        icon="i-lucide-trash-2"
        @click="removeProvider"
      >
        {{ t('actions.delete') }}
      </UButton>
      <UBadge
        v-else-if="draft?.isDefault"
        color="primary"
        variant="subtle"
        class="self-center"
      >
        {{ t('docetra.settings.default') }}
      </UBadge>
    </template>
  </DocumentAppDocumentPage>
</template>
