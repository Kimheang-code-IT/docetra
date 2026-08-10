<script setup lang="ts">
import type {
  AttributeDataType,
  CreateRecordAttributeInput,
  RecordAttribute,
} from '~/types/docetra/configuration'
import { OPTION_DATA_TYPES } from '~/types/docetra/configuration'
import { recordAttributeTabs } from '~/config/configuration-schemas'
import { useConfigurationRepositories } from '~/repositories'
import { useConfirm } from '~/composables/common/useConfirm'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { usePageSeo } from '~/composables/usePageSeo'
import { toConfigCode } from '~/utils/config-code'
import { getByPath, setByPath } from '~/utils/object-path'
import { pushPendingTypeAttributeId } from '~/utils/pending-type-attributes'

const props = defineProps<{
  attributeId?: string
}>()

const isCreate = computed(() => !props.attributeId || props.attributeId === 'new')

const { attributes } = useConfigurationRepositories()
const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const route = useRoute()
const { confirm } = useConfirm()
const { setBreadcrumbs, clear } = useAppHeader()

const returnToType = computed(() => route.query.returnTo === 'type')
const returnTypeId = computed(() => String(route.query.typeId || 'new'))

function listPath() {
  if (returnToType.value) {
    return returnTypeId.value === 'new'
      ? '/configuration/record-types/new'
      : `/configuration/record-types/${returnTypeId.value}`
  }
  return '/configuration/record-attributes'
}

const pending = ref(true)
const saving = ref(false)
const dirty = ref(false)
const hydrating = ref(false)
const activeTab = ref('basic')
const model = ref(emptyAttribute())
const codeTouched = ref(false)

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

async function load() {
  pending.value = true
  hydrating.value = true
  codeTouched.value = !isCreate.value
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
    await nextTick()
    hydrating.value = false
  }
}

function fieldValue(key: string) {
  return getByPath(model.value, key)
}

function setFieldValue(key: string, value: unknown) {
  if (key === 'code') codeTouched.value = true
  setByPath(model.value as any, key, value)

  if (key === 'label' && isCreate.value && !codeTouched.value) {
    model.value.code = toConfigCode(String(value || ''), 'snake')
  }

  if (key === 'dataType' && !OPTION_DATA_TYPES.includes(value as AttributeDataType)) {
    model.value.options = []
  }
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
      if (returnToType.value) {
        if (returnTypeId.value === 'new') {
          pushPendingTypeAttributeId(created.id)
          void router.replace({
            path: '/configuration/record-types/new',
            query: { tab: 'attributes' },
          })
        }
        else {
          void router.replace({
            path: `/configuration/record-types/${returnTypeId.value}`,
            query: { tab: 'attributes', assignAttribute: created.id },
          })
        }
        return
      }
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

async function goBack() {
  if (dirty.value) {
    const ok = await confirm({ kind: 'unsaved' })
    if (!ok) return
    dirty.value = false
  }
  void router.push(listPath())
}

watch(
  () => [isCreate.value, model.value.label, model.value.code, returnToType.value, returnTypeId.value] as const,
  () => {
    const crumbs = returnToType.value
      ? [
          { label: t('docetra.pages.recordType'), to: '/configuration/record-types' },
          {
            label: returnTypeId.value === 'new'
              ? t('docetra.config.createRecordType')
              : t('docetra.pages.recordType'),
            to: listPath(),
          },
          { label: isCreate.value ? t('docetra.config.createRecordAttribute') : (model.value.label || model.value.code || '…') },
        ]
      : [
          { label: t('docetra.pages.recordAttribute'), to: '/configuration/record-attributes' },
          { label: isCreate.value ? t('docetra.config.createRecordAttribute') : (model.value.label || model.value.code || '…') },
        ]
    setBreadcrumbs(crumbs)
  },
  { immediate: true },
)

watch(model, () => {
  if (!hydrating.value) dirty.value = true
}, { deep: true })

onBeforeUnmount(clear)
onMounted(() => void load())
watch(() => props.attributeId, () => void load())

usePageSeo({
  title: () => isCreate.value
    ? t('docetra.config.createRecordAttribute')
    : model.value.label || t('docetra.pages.recordAttribute'),
})
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="tabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending"
    :saving="saving"
    :is-create="isCreate"
    :save-label="isCreate ? t('docetra.common.create') : t('docetra.common.save')"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="true"
    :list-to="listPath()"
    content-wide
    @save="save"
    @refresh="load"
  >
    <template #actions>
      <UButton color="neutral" variant="ghost" @click="goBack">
        {{ t('docetra.common.cancel') }}
      </UButton>
    </template>
  </DocumentAppDocumentPage>
</template>
