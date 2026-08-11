<script setup lang="ts">
import type {
  CreateRecordTypeInput,
  RecordType,
  RecordAttribute,
  RecordTypeAttribute,
} from '~/types/docetra/configuration'
import {
  defaultRecordTypeFeatures,
  defaultRecordTypeNumbering,
} from '~/types/docetra/configuration'
import { recordTypeTabs } from '~/config/configuration-schemas'
import { useConfigurationRepositories } from '~/repositories'
import { useConfirm } from '~/composables/common/useConfirm'
import { useConfigurationDiscussion } from '~/composables/configuration/useConfigurationDiscussion'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { usePageSeo } from '~/composables/usePageSeo'
import { toConfigCode } from '~/utils/config-code'
import { getByPath, setByPath } from '~/utils/object-path'
import {
  clearPendingTypeAttributeIds,
  readPendingTypeAttributeIds,
} from '~/utils/pending-type-attributes'

const props = defineProps<{
  recordTypeId?: string
}>()

const isCreate = computed(() => !props.recordTypeId || props.recordTypeId === 'new')
const { recordTypes, attributes } = useConfigurationRepositories()
const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const route = useRoute()
const { confirm } = useConfirm()
const { setBreadcrumbs, clear } = useAppHeader()
const auth = useAuthStore()
const canEditDocument = computed(() => auth.canAccessPage(permissionForAction(
  'configuration.record_types.view',
  isCreate.value ? 'create' : 'edit',
)))
const canCommentDocument = computed(() => auth.canAccessPage('configuration.record_types.comment'))

const pending = ref(true)
const saving = ref(false)
const dirty = ref(false)
const hydrating = ref(false)
const activeTab = ref('general')
const catalog = ref<RecordAttribute[]>([])
const model = ref(emptyType())
const codeTouched = ref(false)
let attributeSearchToken = 0
const discussionId = computed(() => isCreate.value ? undefined : props.recordTypeId)
const {
  comments,
  activity,
  commentBody,
  submittingComment,
  updatingCommentId,
  deletingCommentId,
  hasMoreFeed,
  loadingMoreFeed,
  currentUser,
  loadDiscussion,
  submitComment,
  updateComment,
  deleteComment,
  loadMoreFeed,
} = useConfigurationDiscussion({ repository: recordTypes, id: discussionId, isCreate })

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
    typeId: isCreate.value ? 'new' : (props.recordTypeId || model.value.id),
    stages: model.value.stages,
    searchAttributes: debouncedAttributeSearch,
  })
  if (!model.value.features.enableWorkflow && activeTab.value === 'workflow') {
    activeTab.value = 'general'
  }
  return next
})

const debouncedAttributeSearch = useDebounceFn(async (query: string) => {
  const token = ++attributeSearchToken
  const response = await attributes.list({
    q: query.trim() || undefined,
    page: 1,
    limit: 50,
    status: 'active',
    sort: 'label',
  })
  if (token !== attributeSearchToken) return
  const assignedIds = new Set(model.value.attributes.map(item => item.attributeId))
  const assignedCatalog = catalog.value.filter(item => assignedIds.has(item.id))
  const known = new Set(assignedCatalog.map(item => item.id))
  catalog.value = [...assignedCatalog, ...(response.data || []).filter(item => !known.has(item.id))]
}, 250)

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

function toAssignment(attr: RecordAttribute, order: number): RecordTypeAttribute {
  return {
    attributeId: attr.id,
    attributeCode: attr.code,
    attributeLabel: attr.label,
    dataType: attr.dataType,
    required: attr.required,
    readOnly: attr.readOnly,
    visible: true,
    searchable: attr.searchable,
    filterable: attr.filterable,
    showInList: attr.showInList,
    section: 'General',
    order,
  }
}

async function assignAttributeIds(ids: string[]) {
  const unique = [...new Set(ids.filter(Boolean))]
  if (!unique.length) return
  const used = new Set(model.value.attributes.map(a => a.attributeId))
  const additions: RecordTypeAttribute[] = []
  for (const id of unique) {
    if (used.has(id)) continue
    let attr = catalog.value.find(a => a.id === id)
    if (!attr) {
      try {
        attr = await attributes.getById(id)
        catalog.value = [...catalog.value, attr]
      }
      catch {
        continue
      }
    }
    additions.push(toAssignment(attr, model.value.attributes.length + additions.length))
    used.add(id)
  }
  if (additions.length) {
    model.value.attributes = [...model.value.attributes, ...additions]
    dirty.value = true
  }
}

async function consumeAssignQueryAndPending() {
  if (route.query.tab === 'attributes') {
    activeTab.value = 'attributes'
  }
  const fromQuery = route.query.assignAttribute
  const queryIds = Array.isArray(fromQuery)
    ? fromQuery.map(String)
    : fromQuery
      ? [String(fromQuery)]
      : []
  const pendingIds = readPendingTypeAttributeIds()
  const ids = [...queryIds, ...pendingIds]
  if (ids.length) {
    await assignAttributeIds(ids)
    clearPendingTypeAttributeIds()
  }
  if (queryIds.length || route.query.tab === 'attributes') {
    const nextQuery = { ...route.query }
    delete nextQuery.assignAttribute
    delete nextQuery.tab
    void router.replace({ query: nextQuery })
  }
}

async function load() {
  pending.value = true
  hydrating.value = true
  codeTouched.value = !isCreate.value
  try {
    const attrRes = await attributes.list({ page: 1, limit: 50, status: 'active', sort: 'label' })
    catalog.value = attrRes.data || []
    if (isCreate.value) {
      model.value = emptyType()
    }
    else {
      const schema = await recordTypes.getResolvedSchema({ id: props.recordTypeId! })
      model.value = schema.recordType
      const known = new Set(catalog.value.map(item => item.id))
      catalog.value = [...catalog.value, ...schema.attributes.filter(item => !known.has(item.id))]
    }
    dirty.value = false
    await consumeAssignQueryAndPending()
    await loadDiscussion()
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
  const stageCodes = new Set(model.value.stages.map(stage => stage.code))
  const invalidStageAssignment = model.value.attributes.find(
    attribute => attribute.stageCode && !stageCodes.has(attribute.stageCode),
  )
  if (invalidStageAssignment) {
    toast.add({
      title: t('docetra.config.invalidAssignedStage', { field: invalidStageAssignment.attributeLabel }),
      color: 'error',
    })
    activeTab.value = 'attributes'
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
watch(
  () => [route.query.assignAttribute, route.query.tab] as const,
  () => {
    if (pending.value || hydrating.value) return
    void consumeAssignQueryAndPending()
  },
)

usePageSeo({
  title: () => isCreate.value
    ? t('docetra.config.createRecordType')
    : model.value.name || t('docetra.pages.recordType'),
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
    :read-only="!canEditDocument"
    :can-save="canEditDocument"
    :is-create="isCreate"
    :save-label="isCreate ? t('docetra.common.create') : t('docetra.common.save')"
    :show-comments="!isCreate"
    :can-comment="canCommentDocument"
    :show-meta-rail="!isCreate"
    :show-list-nav="true"
    list-to="/configuration/record-types"
    :comments="comments"
    :activity="activity"
    :comment-body="commentBody"
    :submitting-comment="submittingComment"
    :updating-comment-id="updatingCommentId"
    :deleting-comment-id="deletingCommentId"
    :has-more-feed="hasMoreFeed"
    :loading-more-feed="loadingMoreFeed"
    :current-user="currentUser"
    :meta-title="model.name"
    :meta-subtitle="model.code"
    :meta-status="model.status"
    :meta-owner="model.updatedBy || null"
    :meta-created-at="model.createdAt"
    :meta-updated-at="model.updatedAt"
    content-wide
    @update:comment-body="commentBody = $event"
    @save="save"
    @refresh="load"
    @submit-comment="submitComment"
    @update-comment="updateComment"
    @delete-comment="deleteComment"
    @load-more-feed="loadMoreFeed"
  >
    <template #actions>
      <UButton color="neutral" variant="ghost" @click="goBack">
        {{ t('docetra.common.cancel') }}
      </UButton>
    </template>
  </DocumentAppDocumentPage>
</template>
