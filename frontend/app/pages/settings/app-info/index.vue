<script setup lang="ts">
import type { AppInfo } from '~/types/docetra/settings'
import { appInfoTabs } from '~/config/settings-schemas'
import { useSettingsRepositories } from '~/repositories'
import { useConfirm } from '~/composables/common/useConfirm'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { useAppBranding } from '~/composables/settings/useAppBranding'
import { getByPath, setByPath } from '~/utils/object-path'

definePageMeta({
  titleKey: 'docetra.pages.appInfo',
})

const { appInfo } = useSettingsRepositories()
const { applyFromAppInfo } = useAppBranding()
const { t } = useI18n()
const toast = useToast()
const { confirm } = useConfirm()
const { setTitle, clear } = useAppHeader()

const pending = ref(true)
const saving = ref(false)
const dirty = ref(false)
const activeTab = ref('info')
const model = ref<AppInfo | null>(null)

async function load() {
  pending.value = true
  try {
    model.value = await appInfo.get()
    applyFromAppInfo(model.value)
    dirty.value = false
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
  }
  finally {
    pending.value = false
  }
}

watch(
  () => model.value?.branding.primaryColor,
  () => {
    if (model.value) applyFromAppInfo(model.value)
  },
)

watch(model, () => { if (model.value) dirty.value = true }, { deep: true })

function fieldValue(key: string) {
  if (!model.value) return undefined
  return getByPath(model.value, key)
}

function setFieldValue(key: string, value: unknown) {
  if (!model.value) return
  setByPath(model.value as any, key, value)
}

async function save() {
  if (!model.value) return
  saving.value = true
  try {
    model.value = await appInfo.update(model.value)
    applyFromAppInfo(model.value)
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

async function reset() {
  const ok = await confirm({
    kind: 'update',
    titleKey: 'docetra.common.reset',
    descriptionKey: 'docetra.confirm.genericDescription',
    confirmLabelKey: 'docetra.common.reset',
    confirmColor: 'warning',
  })
  if (!ok) return

  saving.value = true
  try {
    model.value = await appInfo.reset()
    applyFromAppInfo(model.value)
    dirty.value = false
    toast.add({ title: t('docetra.common.resetDone'), color: 'success' })
  }
  finally {
    saving.value = false
  }
}

onMounted(() => {
  setTitle(t('docetra.pages.appInfo'))
  void load()
})
onBeforeUnmount(clear)

useHead(() => ({ title: `${t('docetra.pages.appInfo')} · ${t('docetra.brand.name')}` }))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="appInfoTabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending || !model"
    :saving="saving"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="false"
    content-wide
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <UButton color="neutral" variant="ghost" :loading="saving" @click="reset">
        {{ t('docetra.common.reset') }}
      </UButton>
    </template>
  </DocumentAppDocumentPage>
</template>
