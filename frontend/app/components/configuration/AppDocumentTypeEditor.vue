<script setup lang="ts">
import type { CreateDocumentTypeInput, DocumentType, DocumentDirection, RecordType } from '~/types/docetra/configuration'
import { documentTypeTabs } from '~/config/configuration-schemas'
import { useConfigurationRepositories } from '~/repositories'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { getByPath, setByPath } from '~/utils/object-path'

const props = defineProps<{
  documentTypeId?: string
}>()

const isCreate = computed(() => !props.documentTypeId || props.documentTypeId === 'new')
const { documentTypes, recordTypes } = useConfigurationRepositories()
const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const { setBreadcrumbs, clear } = useAppHeader()

const pending = ref(true)
const saving = ref(false)
const dirty = ref(false)
const unsavedOpen = ref(false)
const activeTab = ref('details')
const recordTypeOptions = ref<RecordType[]>([])
const model = ref(emptyDoc())

const tabs = computed(() => documentTypeTabs({
  recordTypeOptions: recordTypeOptions.value.map(r => ({ label: r.name, value: r.id })),
}))

function emptyDoc(): DocumentType {
  const now = new Date().toISOString()
  return {
    id: '',
    name: '',
    code: '',
    description: '',
    direction: 'both',
    defaultPriority: 'normal',
    defaultConfidentiality: 'internal',
    allowedFileTypes: ['pdf', 'docx'],
    maxFileSizeMb: 25,
    status: 'active',
    createdAt: now,
    updatedAt: now,
  }
}

async function load() {
  pending.value = true
  try {
    const rt = await recordTypes.list({ limit: 100, status: 'active' })
    recordTypeOptions.value = rt.data || []
    if (isCreate.value) model.value = emptyDoc()
    else model.value = await documentTypes.getById(props.documentTypeId!)
    dirty.value = false
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.loadFailed'), color: 'error' })
    void router.push('/configuration/document-types')
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

const summary = computed(() => ({
  name: model.value.name || '—',
  code: model.value.code || '—',
  direction: model.value.direction,
  related: recordTypeOptions.value.find(r => r.id === model.value.relatedRecordTypeId)?.name || '—',
  files: (model.value.allowedFileTypes || []).join(', ') || '—',
  max: `${model.value.maxFileSizeMb} MB`,
}))

async function save() {
  if (!model.value.name.trim() || !model.value.code.trim()) {
    toast.add({ title: t('docetra.config.requiredIdentity'), color: 'error' })
    return
  }
  saving.value = true
  try {
    const related = recordTypeOptions.value.find(r => r.id === model.value.relatedRecordTypeId)
    const input: CreateDocumentTypeInput = {
      name: model.value.name.trim(),
      code: model.value.code.trim(),
      description: model.value.description,
      direction: model.value.direction as DocumentDirection,
      relatedRecordTypeId: model.value.relatedRecordTypeId,
      defaultPriority: model.value.defaultPriority,
      defaultConfidentiality: model.value.defaultConfidentiality,
      allowedFileTypes: model.value.allowedFileTypes,
      maxFileSizeMb: model.value.maxFileSizeMb,
      status: model.value.status,
    }
    if (isCreate.value) {
      const created = await documentTypes.create(input)
      if (related) await documentTypes.update(created.id, { relatedRecordTypeName: related.name } as any)
      toast.add({ title: t('docetra.common.saved'), color: 'success' })
      dirty.value = false
      void router.replace(`/configuration/document-types/${created.id}`)
    }
    else {
      await documentTypes.update(props.documentTypeId!, {
        ...input,
        relatedRecordTypeName: related?.name,
      } as any)
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
  void router.push('/configuration/document-types')
}

watch(model, () => { dirty.value = true }, { deep: true })
watch(
  () => [isCreate.value, model.value.name] as const,
  () => {
    setBreadcrumbs([
      { label: t('docetra.pages.documentType'), to: '/configuration/document-types' },
      { label: isCreate.value ? t('docetra.common.create') : (model.value.name || '…') },
    ])
  },
  { immediate: true },
)
onBeforeUnmount(clear)
onMounted(() => void load())
watch(() => props.documentTypeId, () => void load())

useHead(() => ({
  title: `${isCreate.value ? t('docetra.common.create') : model.value.name} · ${t('docetra.pages.documentType')}`,
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
      <div class="space-y-3">
        <p class="text-sm font-medium text-highlighted">
          {{ t('docetra.config.summaryPreview') }}
        </p>
        <dl class="space-y-2 text-sm">
          <div>
            <dt class="text-xs text-muted">
              {{ t('docetra.fields.name') }}
            </dt>
            <dd class="font-medium">
              {{ summary.name }}
            </dd>
          </div>
          <div>
            <dt class="text-xs text-muted">
              {{ t('docetra.fields.code') }}
            </dt>
            <dd class="font-medium">
              {{ summary.code }}
            </dd>
          </div>
          <div>
            <dt class="text-xs text-muted">
              {{ t('docetra.config.direction') }}
            </dt>
            <dd class="font-medium capitalize">
              {{ summary.direction }}
            </dd>
          </div>
          <div>
            <dt class="text-xs text-muted">
              {{ t('docetra.config.relatedRecordType') }}
            </dt>
            <dd class="font-medium">
              {{ summary.related }}
            </dd>
          </div>
          <div>
            <dt class="text-xs text-muted">
              {{ t('docetra.config.allowedExtensions') }}
            </dt>
            <dd class="font-medium">
              {{ summary.files }}
            </dd>
          </div>
          <div>
            <dt class="text-xs text-muted">
              {{ t('docetra.config.maxFileSizeMb') }}
            </dt>
            <dd class="font-medium">
              {{ summary.max }}
            </dd>
          </div>
        </dl>
      </div>
    </template>
  </DocumentAppDocumentPage>

  <CommonAppUnsavedChangesDialog
    v-model:open="unsavedOpen"
    @discard="() => { dirty = false; router.push('/configuration/document-types') }"
  />
</template>
