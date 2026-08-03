<script setup lang="ts">
import type { StorageProvider, StorageProviderType } from '~/types/docetra/settings'
import type { ConnectionStatusFieldValue } from '~/types/docetra/common'
import { storageProviderTabs } from '~/config/settings-schemas'
import { useSettingsRepositories } from '~/repositories'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { getByPath, setByPath } from '~/utils/object-path'

definePageMeta({
  titleKey: 'docetra.pages.storage',
})

const { storage } = useSettingsRepositories()
const { t } = useI18n()
const toast = useToast()
const { setTitle, clear } = useAppHeader()

const pending = ref(true)
const saving = ref(false)
const testingId = ref<string | null>(null)
const providers = ref<StorageProvider[]>([])
const selectedId = ref<string | null>(null)
const draft = ref<StorageProvider | null>(null)
const activeTab = ref('provider')

const tabs = computed(() => storageProviderTabs(draft.value?.type))

async function load() {
  pending.value = true
  try {
    providers.value = await storage.list()
    if (!selectedId.value && providers.value[0]) {
      selectProvider(providers.value[0].id)
    }
    else if (selectedId.value) {
      selectProvider(selectedId.value)
    }
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
  }
  finally {
    pending.value = false
  }
}

function selectProvider(id: string) {
  selectedId.value = id
  const found = providers.value.find(p => p.id === id)
  draft.value = found ? structuredClone(found) : null
}

function fieldValue(key: string): unknown {
  if (!draft.value) return undefined

  if (key === '__storageConnection') {
    const value: ConnectionStatusFieldValue = {
      status: draft.value.connectionStatus,
      message: draft.value.lastTestMessage,
      lastTestedAt: draft.value.lastTestedAt,
      details: [
        { label: t('docetra.settings.providerType'), value: draft.value.type },
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

async function setDefault(id: string) {
  try {
    await storage.setDefault(id)
    toast.add({ title: t('docetra.settings.defaultUpdated'), color: 'success' })
    await load()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
}

async function testConnection(id: string) {
  testingId.value = id
  try {
    const result = await storage.testConnection(id)
    toast.add({
      title: result.message,
      color: result.status === 'connected' ? 'success' : 'error',
    })
    await load()
  }
  finally {
    testingId.value = null
  }
}

function providerIcon(type: StorageProviderType) {
  const map: Record<StorageProviderType, string> = {
    local: 'i-lucide-hard-drive',
    cloudflare_r2: 'i-lucide-cloud',
    amazon_s3: 'i-lucide-box',
    minio: 'i-lucide-server',
    google_drive: 'i-lucide-folder-sync',
  }
  return map[type]
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
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="false"
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <CommonAppConnectionTestButton
        v-if="draft"
        :loading="testingId === draft.id"
        @click="testConnection(draft.id)"
      />
      <UButton
        v-if="draft && !draft.isDefault"
        color="neutral"
        variant="soft"
        icon="i-lucide-star"
        @click="setDefault(draft.id)"
      >
        {{ t('docetra.settings.setDefault') }}
      </UButton>
    </template>

    <template #before-form>
      <div class="grid gap-3 px-4 pt-4 sm:px-6 md:grid-cols-2 xl:grid-cols-3">
        <button
          v-for="provider in providers"
          :key="provider.id"
          type="button"
          class="rounded-lg border p-4 text-left transition"
          :class="selectedId === provider.id ? 'border-primary bg-primary/5' : 'border-default bg-default hover:border-primary/40'"
          @click="selectProvider(provider.id)"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2">
              <div class="flex size-9 items-center justify-center rounded-lg bg-elevated">
                <UIcon :name="providerIcon(provider.type)" class="size-4" />
              </div>
              <div>
                <p class="text-sm font-semibold">
                  {{ provider.name }}
                </p>
                <p class="text-xs capitalize text-muted">
                  {{ provider.type.replaceAll('_', ' ') }}
                </p>
              </div>
            </div>
            <UBadge v-if="provider.isDefault" color="primary" variant="subtle" size="sm">
              {{ t('docetra.settings.default') }}
            </UBadge>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            <CommonAppStatusBadge :status="provider.connectionStatus" />
            <UBadge :color="provider.active ? 'success' : 'neutral'" variant="subtle" size="sm">
              {{ provider.active ? t('docetra.status.active') : t('docetra.status.disabled') }}
            </UBadge>
          </div>
          <p class="mt-2 truncate text-xs text-muted">
            {{ provider.bucket || provider.folderId || provider.uploadPathPattern }}
          </p>
        </button>
      </div>
    </template>
  </DocumentAppDocumentPage>
</template>
