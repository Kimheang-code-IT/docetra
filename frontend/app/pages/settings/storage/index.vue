<script setup lang="ts">
import type { StorageProvider, StorageProviderType } from '~/types/docetra/settings'
import type { ConnectionStatusFieldValue } from '~/types/docetra/common'
import { storageSettingsTabs } from '~/config/settings-schemas'
import { useSettingsRepositories } from '~/repositories'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { getByPath, setByPath } from '~/utils/object-path'

definePageMeta({
  titleKey: 'docetra.pages.storage',
})

const STORAGE_TAB_TYPES = storageSettingsTabs.map(tab => tab.id) as StorageProviderType[]

const { storage } = useSettingsRepositories()
const { t } = useI18n()
const toast = useToast()
const { setTitle, clear } = useAppHeader()

const pending = ref(true)
const saving = ref(false)
const testing = ref(false)
const providers = ref<StorageProvider[]>([])
const draft = ref<StorageProvider | null>(null)
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

  return getByPath(draft.value, key)
}

function setFieldValue(key: string, value: unknown) {
  if (!draft.value) return
  if (key === '__storageConnection' || key === 'type') return
  setByPath(draft.value as any, key, value)
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

onMounted(() => {
  setTitle(t('docetra.pages.storage'))
  void load()
})
onBeforeUnmount(clear)

useHead(() => ({ title: `${t('docetra.pages.storage')} · ${t('docetra.brand.name')}` }))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="tabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending"
    :saving="saving"
    :can-save="Boolean(draft)"
    :error="!pending && !draft ? t('docetra.common.loadFailed') : null"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="false"
    content-wide
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <CommonAppConnectionTestButton
        v-if="draft"
        :loading="testing"
        @click="testConnection"
      />
      <UButton
        v-if="draft && !draft.isDefault"
        color="neutral"
        variant="soft"
        icon="i-lucide-star"
        @click="setDefault"
      >
        {{ t('docetra.settings.setDefault') }}
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
