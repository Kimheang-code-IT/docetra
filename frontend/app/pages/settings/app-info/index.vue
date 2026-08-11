<script setup lang="ts">
import type { AppInfo } from '~/types/docetra/settings'
import { appInfoTabs } from '~/config/settings-schemas'
import { useSettingsRepositories } from '~/repositories'
import { useConfirm } from '~/composables/common/useConfirm'
import { usePathModel } from '~/composables/common/usePathModel'
import { useAppPageTitle } from '~/composables/layout/useAppPageTitle'
import { useAppBranding } from '~/composables/settings/useAppBranding'

definePageMeta({
  titleKey: 'docetra.pages.appInfo',
  permission: 'settings.app_info.view',
})

const { appInfo } = useSettingsRepositories()
const { applyFromAppInfo } = useAppBranding()
const { t } = useI18n()
const toast = useToast()
const { confirm } = useConfirm()
const auth = useAuthStore()
const canEdit = computed(() => auth.canAccessPage('settings.app_info.edit'))
const canConfigure = computed(() => auth.canAccessPage('settings.app_info.configure'))

const pending = ref(true)
const saving = ref(false)
const activeTab = ref('info')
const model = ref<AppInfo | null>(null)
const { fieldValue, setFieldValue } = usePathModel(model)

async function load() {
  pending.value = true
  try {
    model.value = await appInfo.get()
    applyFromAppInfo(model.value)
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

async function save() {
  if (!model.value) return
  saving.value = true
  try {
    model.value = await appInfo.update(model.value)
    applyFromAppInfo(model.value)
    toast.add({ title: t('docetra.common.saved'), color: 'success' })
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
    toast.add({ title: t('docetra.common.resetDone'), color: 'success' })
  }
  finally {
    saving.value = false
  }
}

onMounted(() => void load())
useAppPageTitle(() => t('docetra.pages.appInfo'))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="appInfoTabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending || !model"
    :saving="saving"
    :read-only="!canEdit"
    :can-save="canEdit"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="false"
    content-wide
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <UButton v-if="canConfigure" color="neutral" variant="ghost" :loading="saving" @click="reset">
        {{ t('docetra.common.reset') }}
      </UButton>
    </template>
  </DocumentAppDocumentPage>
</template>
