<script setup lang="ts">
import type { AppInfo } from '~/types/docetra/settings'
import { appInfoTabs } from '~/config/settings-schemas'
import { useSettingsRepositories } from '~/repositories'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { getByPath, setByPath } from '~/utils/object-path'

definePageMeta({
  titleKey: 'docetra.pages.appInfo',
})

const { appInfo } = useSettingsRepositories()
const { t } = useI18n()
const toast = useToast()
const { setTitle, clear } = useAppHeader()

const pending = ref(true)
const saving = ref(false)
const dirty = ref(false)
const unsavedOpen = ref(false)
const activeTab = ref('info')
const model = ref<AppInfo | null>(null)

async function load() {
  pending.value = true
  try {
    model.value = await appInfo.get()
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
  saving.value = true
  try {
    model.value = await appInfo.reset()
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
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <UButton color="neutral" variant="ghost" :loading="saving" @click="reset">
        {{ t('docetra.common.reset') }}
      </UButton>
    </template>

    <template v-if="model" #aside>
      <div class="space-y-3 text-center">
        <p class="text-left text-sm font-medium text-highlighted">
          {{ t('docetra.common.preview') }}
        </p>
        <div
          class="mx-auto flex size-16 items-center justify-center rounded-xl"
          :style="{ backgroundColor: model.branding.primaryColor || '#2563eb' }"
        >
          <img
            v-if="model.branding.mainLogoUrl"
            :src="model.branding.mainLogoUrl"
            alt=""
            class="max-h-12 max-w-12 object-contain"
          >
          <span v-else class="text-lg font-bold text-white">
            {{ (model.shortName || 'D').slice(0, 2) }}
          </span>
        </div>
        <div>
          <p class="text-base font-semibold">
            {{ model.applicationName }}
          </p>
          <p class="text-xs text-muted">
            {{ model.organizationName }}
          </p>
        </div>
        <p class="text-xs text-muted">
          {{ model.footer.copyrightText }}
        </p>
      </div>
    </template>
  </DocumentAppDocumentPage>

  <CommonAppUnsavedChangesDialog v-model:open="unsavedOpen" />
</template>
