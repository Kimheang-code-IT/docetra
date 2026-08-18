<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'
import { useDocumentPage } from '~/composables/workspace/useDocumentPage'
import { useRecordTypeDrivenTabs } from '~/composables/record/useRecordTypeDrivenTabs'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { usePageSeo } from '~/composables/usePageSeo'
import { getByPath } from '~/utils/object-path'
import type { ExportRequest } from '~/types/docetra/export'
import { createExportJob } from '~/adapters/exports'

const props = defineProps<{
  config: EntityConfig
}>()

const {
  isCreate,
  model,
  pending,
  saving,
  error,
  notFound,
  dirty,
  title,
  activeTab,
  comments,
  activity,
  attachments,
  hasMoreFeed,
  loadingMoreFeed,
  commentBody,
  submittingComment,
  updatingCommentId,
  deletingCommentId,
  previousRecordId,
  nextRecordId,
  loadingRecordNavigation,
  recordNavigationDirection,
  isFavorite,
  togglingFavorite,
  fieldValue,
  setFieldValue,
  load,
  save,
  submitComment,
  updateComment,
  deleteComment,
  loadMoreFeed,
  navigatePreviousRecord,
  navigateNextRecord,
  toggleFavorite,
} = useDocumentPage(props.config)

const {
  tabs: documentTabs,
  loadingType: loadingRecordSchema,
  reload: reloadRecordSchema,
} = useRecordTypeDrivenTabs({
  entityKey: props.config.key,
  recordBacked: props.config.recordBacked === true,
  recordTypeCode: props.config.recordTypeCode,
  baseTabs: props.config.tabs,
  getRecordTypeId: () => {
    const id = model.value.recordTypeId
    return id == null || id === '' ? undefined : String(id)
  },
  getDetails: () => {
    const raw = model.value.details
    return raw && typeof raw === 'object' && !Array.isArray(raw)
      ? { ...(raw as Record<string, unknown>) }
      : {}
  },
  setDetails: (details) => {
    setFieldValue('details', details)
  },
  setStageIfEmpty: (stage) => {
    if (isCreate.value || !getByPath(model.value, 'stage')) {
      setFieldValue('stage', stage)
    }
  },
})

const { t, te } = useI18n()
const auth = useAuthStore()
const { setBreadcrumbs, setBadges, clear } = useAppHeader()
const toast = useToast()

const statusLabel = computed(() => {
  const status = String(model.value.status || '')
  if (!status) return ''
  const key = `docetra.status.${status}`
  return te(key) ? t(key) : status
})

const codeOrRef = computed(() =>
  String(model.value.code || model.value.referenceNumber || model.value.id || ''),
)

watch(
  [title, isCreate, statusLabel, dirty, () => props.config],
  () => {
    setBreadcrumbs([
      {
        label: t(props.config.groupKey),
        to: props.config.routeBase,
      },
      {
        label: t(props.config.titleKey),
        to: props.config.routeBase,
      },
      {
        label: title.value,
      },
    ])

    const nextBadges: { label: string, color: 'info' | 'warning' }[] = []
    if (statusLabel.value) {
      nextBadges.push({ label: statusLabel.value, color: 'info' })
    }
    if (dirty.value) {
      nextBadges.push({ label: t('docetra.document.unsaved'), color: 'warning' })
    }
    setBadges(nextBadges)
  },
  { immediate: true, deep: true },
)

onBeforeUnmount(clear)

onDeactivated(clear)

usePageSeo({
  title: () => title.value,
})

const canDuplicateDocument = computed(() => auth.canAccessPage(permissionForAction(
  props.config.permission,
  'create',
)))

const moreItems = computed(() => canDuplicateDocument.value ? [[
  {
    label: t('docetra.document.duplicate'),
    icon: 'i-lucide-copy',
    disabled: isCreate.value,
    onSelect: () => toast.add({ title: t('docetra.document.comingSoon'), color: 'neutral' }),
  },
]] : [])

const currentUser = computed(() => ({
  id: String(auth.user?.id || auth.user?.email || 'current'),
  name: auth.user?.name || 'You',
  email: auth.user?.email,
}))

const showMetaRail = computed(() => props.config.document?.metaRail !== false)
const contentWide = computed(() => props.config.document?.wide === true)
// Dynamic schema loading must not cover a new form with the full-page pending
// overlay. Existing records still block until both record and schema are ready.
const documentPending = computed(() =>
  !isCreate.value && (pending.value || loadingRecordSchema.value),
)
const exporting = ref(false)
const canEditDocument = computed(() => auth.canAccessPage(permissionForAction(
  props.config.permission,
  isCreate.value ? 'create' : 'edit',
)))
const canCommentDocument = computed(() => props.config.canComment !== false
  && auth.canAccessPage(permissionForAction(props.config.permission, 'comment')))
const canExportDocument = computed(() => auth.canAccessPage(permissionForAction(props.config.permission, 'export')))

async function exportDocument(request: ExportRequest) {
  exporting.value = true
  try {
    await createExportJob({
      ...request,
      resource: props.config.key,
      format: 'csv',
      query: isCreate.value ? undefined : { id: String(model.value.id || '') },
      selectedIds: isCreate.value ? undefined : [String(model.value.id || '')],
    })
  }
  finally { exporting.value = false }
}

/** One save path validates the same resolved schema that renders the form. */
function saveDocument() {
  return save(documentTabs.value)
}

/** Reload the record first, then its current Record Type schema and related data. */
async function refreshDocument() {
  await load()
  await reloadRecordSchema()
}
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="documentTabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="documentPending"
    :saving="saving"
    :error="error"
    :not-found="notFound"
    :read-only="config.readOnly || !canEditDocument"
    :show-comments="!isCreate"
    :show-meta-rail="showMetaRail"
    :content-wide="contentWide"
    :show-list-nav="true"
    :can-navigate-previous="Boolean(previousRecordId)"
    :can-navigate-next="Boolean(nextRecordId)"
    :loading-list-navigation="loadingRecordNavigation"
    :list-navigation-direction="recordNavigationDirection"
    :list-to="config.routeBase"
    :is-create="isCreate"
    :can-comment="canCommentDocument"
    :can-export="canExportDocument"
    :comments="comments"
    :activity="activity"
    :attachments="attachments"
    :comment-body="commentBody"
    :submitting-comment="submittingComment"
    :updating-comment-id="updatingCommentId"
    :deleting-comment-id="deletingCommentId"
    :has-more-feed="hasMoreFeed"
    :loading-more-feed="loadingMoreFeed"
    :current-user="currentUser"
    :meta-title="title"
    :meta-subtitle="codeOrRef"
    :meta-status="statusLabel"
    :meta-stage="model.stage ? String(model.stage) : undefined"
    :meta-owner="(model.owner as any) || null"
    :meta-assignee="(model.assignee as any) || null"
    :meta-tags="(model.tags as string[]) || []"
    :meta-created-at="model.createdAt ? String(model.createdAt) : undefined"
    :meta-updated-at="model.updatedAt ? String(model.updatedAt) : undefined"
    :meta-favorite="isFavorite"
    :toggling-favorite="togglingFavorite"
    :more-items="moreItems"
    :exporting="exporting"
    @update:comment-body="commentBody = $event"
    @update:attachments="attachments = $event"
    @save="saveDocument"
    @refresh="refreshDocument"
    @submit-comment="submitComment"
    @update-comment="updateComment"
    @delete-comment="deleteComment"
    @load-more-feed="loadMoreFeed"
    @navigate-previous="navigatePreviousRecord"
    @navigate-next="navigateNextRecord"
    @toggle-favorite="toggleFavorite"
    @export="exportDocument"
  />
</template>
