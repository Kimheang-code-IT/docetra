<script setup lang="ts">
import type { AppConfig } from '~/types/docetra/settings'
import type { ConnectionStatusFieldValue } from '~/types/docetra/common'
import { appConfigTabs } from '~/config/settings-schemas'
import { useSettingsRepositories } from '~/repositories'
import { useConfirm } from '~/composables/common/useConfirm'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { getByPath, setByPath } from '~/utils/object-path'

definePageMeta({
  titleKey: 'docetra.pages.appConfig',
})

const { appConfig } = useSettingsRepositories()
const { t } = useI18n()
const toast = useToast()
const { confirm } = useConfirm()
const { setTitle, clear } = useAppHeader()

const pending = ref(true)
const saving = ref(false)
const testingEmail = ref(false)
const testingTelegram = ref(false)
const dirty = ref(false)
const activeTab = ref('general')
const model = ref<AppConfig | null>(null)

async function load() {
  pending.value = true
  try {
    model.value = await appConfig.get()
    dirty.value = false
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
  }
  finally {
    pending.value = false
  }
}

watch(model, () => { if (model.value) dirty.value = true }, { deep: true })

function fieldValue(key: string): unknown {
  if (!model.value) return undefined

  if (key === '__emailConnection') {
    const value: ConnectionStatusFieldValue = {
      status: model.value.email.connectionStatus,
      message: model.value.email.lastTestMessage,
      lastTestedAt: model.value.email.lastTestedAt,
    }
    return value
  }

  if (key === '__telegramConnection') {
    const value: ConnectionStatusFieldValue = {
      status: model.value.telegram.connectionStatus,
      message: model.value.telegram.lastTestMessage,
      lastTestedAt: model.value.telegram.lastTestedAt,
      details: model.value.telegram.botUsername
        ? [{ label: t('docetra.settings.botUsername'), value: model.value.telegram.botUsername }]
        : [],
    }
    return value
  }

  if (key === '__securityAlert') return null

  // Select options use string values; coerce number fields for USelect match.
  if (key === 'general.defaultPageSize' || key === 'system.paginationDefault') {
    const raw = getByPath(model.value, key)
    return raw == null || raw === '' ? undefined : String(raw)
  }

  return getByPath(model.value, key)
}

async function setFieldValue(key: string, value: unknown) {
  if (!model.value) return

  if (key === '__emailConnection' || key === '__telegramConnection' || key === '__securityAlert') {
    return
  }

  if (key === 'system.maintenanceMode' || key === 'system.readOnlyMode') {
    if (value === true) {
      const ok = await confirm({
        kind: 'update',
        titleKey: 'docetra.settings.confirmModeTitle',
        descriptionKey: 'docetra.settings.confirmModeHelp',
        confirmColor: 'warning',
      })
      if (!ok) return
    }
    setByPath(model.value as any, key, value)
    return
  }

  if (key === 'general.defaultPageSize' || key === 'system.paginationDefault') {
    const n = Number(value)
    setByPath(model.value as any, key, Number.isFinite(n) ? n : 20)
    return
  }

  setByPath(model.value as any, key, value)
}

async function save() {
  if (!model.value) return
  saving.value = true
  try {
    model.value = await appConfig.update(model.value)
    const { invalidateCardFieldsCache } = await import('~/composables/settings/useCardFields')
    invalidateCardFieldsCache()
    toast.add({ title: t('docetra.common.saved'), color: 'success' })
    dirty.value = false
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.saveFailed'), color: 'error' })
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

onMounted(() => {
  setTitle(t('docetra.pages.appConfig'))
  void load()
})
onBeforeUnmount(clear)

useHead(() => ({ title: `${t('docetra.pages.appConfig')} · ${t('docetra.brand.name')}` }))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="appConfigTabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending || !model"
    :saving="saving"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="false"
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <CommonAppConnectionTestButton
        v-if="activeTab === 'email'"
        :loading="testingEmail"
        @click="testEmail"
      />
      <CommonAppConnectionTestButton
        v-if="activeTab === 'telegram'"
        :loading="testingTelegram"
        @click="testTelegram"
      />
    </template>
  </DocumentAppDocumentPage>
</template>
