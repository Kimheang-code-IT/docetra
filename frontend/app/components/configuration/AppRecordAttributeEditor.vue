<script setup lang="ts">
import type {
  AttributeDataType,
  CreateRecordAttributeInput,
  RecordAttribute,
} from '~/types/docetra/configuration'
import { OPTION_DATA_TYPES } from '~/types/docetra/configuration'
import { recordAttributeTabs } from '~/config/configuration-schemas'
import { useConfigurationRepositories } from '~/repositories'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { getByPath, setByPath } from '~/utils/object-path'

const props = defineProps<{
  attributeId?: string
}>()

const isCreate = computed(() => !props.attributeId || props.attributeId === 'new')

const { attributes } = useConfigurationRepositories()
const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const { setBreadcrumbs, clear } = useAppHeader()

const pending = ref(true)
const saving = ref(false)
const dirty = ref(false)
const unsavedOpen = ref(false)
const activeTab = ref('basic')
const model = ref(emptyAttribute())

const showOptions = computed(() => OPTION_DATA_TYPES.includes(model.value.dataType))

const tabs = computed(() => {
  const next = recordAttributeTabs({
    showOptions: showOptions.value,
    dataType: model.value.dataType as AttributeDataType,
    codeReadOnly: !isCreate.value && model.value.usedByCount > 0,
    visibilityFieldOptions: [
      { label: model.value.label || model.value.code || '—', value: model.value.code },
    ],
  })
  if (!showOptions.value && activeTab.value === 'options') {
    activeTab.value = 'basic'
  }
  return next
})

function emptyAttribute(): RecordAttribute {
  const now = new Date().toISOString()
  return {
    id: '',
    label: '',
    code: '',
    name: '',
    description: '',
    helpText: '',
    dataType: 'short_text',
    placeholder: '',
    required: false,
    unique: false,
    readOnly: false,
    searchable: true,
    filterable: false,
    sortable: false,
    showInList: true,
    validation: {},
    options: [],
    visibility: null,
    usedByCount: 0,
    status: 'active',
    createdAt: now,
    updatedAt: now,
  }
}

watch(model, () => { dirty.value = true }, { deep: true })

async function load() {
  pending.value = true
  try {
    if (isCreate.value) {
      model.value = emptyAttribute()
    }
    else {
      model.value = await attributes.getById(props.attributeId!)
    }
    dirty.value = false
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
    void router.push('/configuration/record-attributes')
  }
  finally {
    pending.value = false
  }
}

function fieldValue(key: string) {
  return getByPath(model.value, key)
}

function setFieldValue(key: string, value: unknown) {
  setByPath(model.value as any, key, value)
}

function toInput(): CreateRecordAttributeInput {
  const m = model.value
  return {
    label: m.label.trim(),
    code: m.code.trim(),
    name: m.label.trim(),
    description: m.description,
    helpText: m.helpText,
    dataType: m.dataType,
    placeholder: m.placeholder,
    defaultValue: m.defaultValue,
    required: m.required,
    unique: m.unique,
    readOnly: m.readOnly,
    searchable: m.searchable,
    filterable: m.filterable,
    sortable: m.sortable,
    showInList: m.showInList,
    validation: m.validation,
    options: showOptions.value ? m.options : [],
    visibility: m.visibility,
    status: m.status,
  }
}

async function save() {
  if (!model.value.label.trim() || !model.value.code.trim()) {
    toast.add({ title: t('docetra.config.requiredIdentity'), color: 'error' })
    activeTab.value = 'basic'
    return
  }
  saving.value = true
  try {
    if (isCreate.value) {
      const created = await attributes.create(toInput())
      toast.add({ title: t('docetra.common.saved'), color: 'success' })
      dirty.value = false
      void router.replace(`/configuration/record-attributes/${created.id}`)
    }
    else {
      await attributes.update(props.attributeId!, toInput())
      toast.add({ title: t('docetra.common.saved'), color: 'success' })
      dirty.value = false
      await load()
    }
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.saveFailed'), color: 'error' })
  }
  finally {
    saving.value = false
  }
}

function goBack() {
  if (dirty.value) {
    unsavedOpen.value = true
    return
  }
  void router.push('/configuration/record-attributes')
}

function discardAndLeave() {
  dirty.value = false
  void router.push('/configuration/record-attributes')
}

watch(
  () => [isCreate.value, model.value.label, model.value.code] as const,
  () => {
    setBreadcrumbs([
      { label: t('docetra.pages.recordAttribute'), to: '/configuration/record-attributes' },
      { label: isCreate.value ? t('docetra.common.create') : (model.value.label || model.value.code || '…') },
    ])
  },
  { immediate: true },
)

onBeforeUnmount(clear)
onMounted(() => void load())
watch(() => props.attributeId, () => void load())

useHead(() => ({
  title: `${isCreate.value ? t('docetra.common.create') : model.value.label} · ${t('docetra.pages.recordAttribute')}`,
}))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="tabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending"
    :saving="saving"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="false"
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <UButton color="neutral" variant="ghost" @click="goBack">
        {{ t('docetra.common.cancel') }}
      </UButton>
    </template>

    <template #aside>
      <ConfigurationAppDynamicFieldPreview :attribute="model" />
    </template>
  </DocumentAppDocumentPage>

  <CommonAppUnsavedChangesDialog
    v-model:open="unsavedOpen"
    @discard="discardAndLeave"
  />
</template>
