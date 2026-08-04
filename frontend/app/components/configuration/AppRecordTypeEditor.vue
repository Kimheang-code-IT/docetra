<script setup lang="ts">
import type {
  CreateRecordTypeInput,
  RecordType,
  RecordAttribute,
} from '~/types/docetra/configuration'
import {
  defaultRecordTypeFeatures,
  defaultRecordTypeNumbering,
} from '~/types/docetra/configuration'
import { recordTypeTabs } from '~/config/configuration-schemas'
import { useConfigurationRepositories } from '~/repositories'
import { useConfirm } from '~/composables/common/useConfirm'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { toConfigCode } from '~/utils/config-code'
import { getByPath, setByPath } from '~/utils/object-path'

const props = defineProps<{
  recordTypeId?: string
}>()

const isCreate = computed(() => !props.recordTypeId || props.recordTypeId === 'new')
const { recordTypes, attributes } = useConfigurationRepositories()
const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const { confirm } = useConfirm()
const { setBreadcrumbs, clear } = useAppHeader()

const pending = ref(true)
const saving = ref(false)
const dirty = ref(false)
const hydrating = ref(false)
const activeTab = ref('general')
const catalog = ref<RecordAttribute[]>([])
const model = ref(emptyType())
const codeTouched = ref(false)

const availableAttributeOptions = computed(() => {
  const used = new Set(model.value.attributes.map(a => a.attributeId))
  return catalog.value
    .filter(a => a.status === 'active' && !used.has(a.id))
    .map(a => ({
      label: `${a.label} (${a.code})`,
      value: a.id,
    }))
})

const tabs = computed(() => {
  const next = recordTypeTabs({
    attributeCatalog: catalog.value,
    availableAttributeOptions: availableAttributeOptions.value,
    enableWorkflow: model.value.features.enableWorkflow,
  })
  if (!model.value.features.enableWorkflow && activeTab.value === 'workflow') {
    activeTab.value = 'general'
  }
  return next
})

function emptyType(): RecordType {
  const now = new Date().toISOString()
  return {
    id: '',
    name: '',
    code: '',
    description: '',
    icon: 'i-lucide-shapes',
    color: '#2563eb',
    status: 'active',
    features: defaultRecordTypeFeatures(),
    numbering: defaultRecordTypeNumbering('DOC'),
    attributes: [],
    stages: [],
    transitions: [],
    attributeCount: 0,
    workflowEnabled: true,
    createdAt: now,
    updatedAt: now,
  }
}

async function load() {
  pending.value = true
  hydrating.value = true
  codeTouched.value = !isCreate.value
  try {
    const attrRes = await attributes.list({ limit: 200, status: 'active' })
    catalog.value = attrRes.data || []
    if (isCreate.value) {
      model.value = emptyType()
    }
    else {
      model.value = await recordTypes.getById(props.recordTypeId!)
    }
    dirty.value = false
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
    void router.push('/configuration/record-types')
  }
  finally {
    pending.value = false
    await nextTick()
    hydrating.value = false
  }
}

function fieldValue(key: string) {
  if (key === '__workflow') {
    return {
      stages: model.value.stages,
      transitions: model.value.transitions,
    }
  }
  return getByPath(model.value, key)
}

function setFieldValue(key: string, value: unknown) {
  if (key === 'code') codeTouched.value = true
  if (key === '__workflow') {
    const payload = value as { stages?: any[], transitions?: any[] }
    model.value.stages = payload.stages || []
    model.value.transitions = payload.transitions || []
    return
  }
  setByPath(model.value as any, key, value)

  if (key === 'name' && isCreate.value && !codeTouched.value) {
    const code = toConfigCode(String(value || ''), 'snake')
    model.value.code = code
    if (code) {
      model.value.numbering = {
        ...model.value.numbering,
        prefix: toConfigCode(String(value || ''), 'upper').slice(0, 8) || 'DOC',
      }
    }
  }

  if (key === 'features.enableWorkflow') {
    model.value.workflowEnabled = Boolean(value)
  }
}

function toInput(): CreateRecordTypeInput {
  const m = model.value
  return {
    name: m.name.trim(),
    code: m.code.trim(),
    description: m.description,
    icon: m.icon,
    color: m.color,
    features: m.features,
    numbering: m.numbering,
    attributes: m.attributes,
    stages: m.features.enableWorkflow ? m.stages : [],
    transitions: m.features.enableWorkflow ? m.transitions : [],
    status: m.status,
  }
}

async function save() {
  if (!model.value.name.trim() || !model.value.code.trim()) {
    toast.add({ title: t('docetra.config.requiredIdentity'), color: 'error' })
    activeTab.value = 'general'
    return
  }
  saving.value = true
  try {
    if (isCreate.value) {
      const created = await recordTypes.create(toInput())
      toast.add({ title: t('docetra.common.saved'), color: 'success' })
      dirty.value = false
      void router.replace(`/configuration/record-types/${created.id}`)
    }
    else {
      await recordTypes.update(props.recordTypeId!, toInput())
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
  void router.push('/configuration/record-types')
}

watch(
  () => [isCreate.value, model.value.name] as const,
  () => {
    setBreadcrumbs([
      { label: t('docetra.pages.recordType'), to: '/configuration/record-types' },
      { label: isCreate.value ? t('docetra.config.createRecordType') : (model.value.name || '…') },
    ])
  },
  { immediate: true },
)

watch(model, () => {
  if (!hydrating.value) dirty.value = true
}, { deep: true })

onBeforeUnmount(clear)
onMounted(() => void load())
watch(() => props.recordTypeId, () => void load())

useHead(() => ({
  title: `${isCreate.value ? t('docetra.config.createRecordType') : model.value.name} · ${t('docetra.pages.recordType')}`,
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
    :is-create="isCreate"
    :save-label="isCreate ? t('docetra.common.create') : t('docetra.common.save')"
    :show-comments="false"
    :show-meta-rail="false"
    :show-list-nav="true"
    list-to="/configuration/record-types"
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
