<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'
import { getAdapterForConfig } from '~/config/entities'
import { useDocumentPage } from '~/composables/workspace/useDocumentPage'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { useRecordTypeDrivenTabs } from '~/composables/record/useRecordTypeDrivenTabs'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { usePageSeo } from '~/composables/usePageSeo'
import { getByPath } from '~/utils/object-path'
import type { ExportRequest } from '~/types/docetra/export'
import { useExportJobRunner } from '~/composables/common/useExportJobRunner'
import { resolveCreateReturnTo } from '~/utils/workspace-list-stale'
import {
  MEETING_COMPLETED_STAGE,
  isCompletedMeeting,
  meetingDetailOpenedFromTopics,
  meetingHistoryDetailPath,
} from '~/utils/meeting/detail-route'

const props = defineProps<{
  config: EntityConfig
}>()

const {
  isCreate,
  id,
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
} = useDocumentPage(props.config)

// Existing records upload+attach in one call; create mode uploads to the file
// store and links the real files when the record is saved.
function onAttachmentAttached(version: number | undefined) {
  // Upload+attach bumped the server version; keep the local model in sync so
  // the next save does not fail with a 409 conflict.
  if (version != null) model.value = { ...model.value, version }
}

const attachmentUploadEndpoint = computed(() =>
  isCreate.value
    ? ApiEndpoints.FILE_UPLOADS
    : ApiEndpoints.RECORD_ATTACHMENT_UPLOAD(String(props.config.recordTypeCode || props.config.key), String(id.value)),
)

const {
  tabs: documentTabs,
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

const { t } = useI18n()
const auth = useAuthStore()
const exportRunner = useExportJobRunner()
const { setBreadcrumbs, setBadges, clear } = useAppHeader()
const toast = useToast()

const codeOrRef = computed(() =>
  String(model.value.code || model.value.referenceNumber || model.value.id || ''),
)

const route = useRoute()
const openedFromTopics = computed(() =>
  props.config.key === 'meetingHistory'
  && meetingDetailOpenedFromTopics(resolveCreateReturnTo(route.query.returnTo, '')),
)

watch(
  [title, isCreate, dirty, () => props.config, openedFromTopics],
  () => {
    const listTo = openedFromTopics.value ? '/meetings/topics' : props.config.routeBase
    const listLabel = openedFromTopics.value
      ? t('docetra.pages.meetingTopic')
      : t(props.config.titleKey)
    setBreadcrumbs([
      {
        label: t(props.config.groupKey),
        to: listTo,
      },
      {
        label: listLabel,
        to: listTo,
      },
      {
        label: title.value,
      },
    ])

    const nextBadges: { label: string, color: 'info' | 'warning' }[] = []
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

const moreItems = computed(() => {
  const items: Array<Array<Record<string, unknown>>> = []
  if (canDuplicateDocument.value) {
    items.push([{
      label: t('docetra.document.duplicate'),
      icon: 'i-lucide-copy',
      disabled: isCreate.value,
      onSelect: () => toast.add({ title: t('docetra.document.comingSoon'), color: 'neutral' }),
    }])
  }
  if (
    openedFromTopics.value
    && canEditDocument.value
    && !isCreate.value
    && !isCompletedMeeting(model.value.stage)
  ) {
    items.push([{
      label: t('docetra.meetingBoard.moveToHistory'),
      icon: 'i-lucide-history',
      onSelect: () => void moveMeetingToHistory(),
    }])
  }
  return items
})

async function moveMeetingToHistory() {
  const adapter = getAdapterForConfig(props.config)
  if (!adapter.transitionStage || !id.value) return
  try {
    await adapter.transitionStage(id.value, MEETING_COMPLETED_STAGE, {
      version: typeof model.value.version === 'number' ? model.value.version : undefined,
    })
    toast.add({ title: t('docetra.meetingBoard.movedToHistory'), color: 'success' })
    await navigateTo(meetingHistoryDetailPath(id.value))
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
}

const currentUser = computed(() => ({
  id: String(auth.user?.id || auth.user?.email || 'current'),
  name: auth.user?.name || 'You',
  email: auth.user?.email,
}))

const showMetaRail = computed(() => props.config.document?.metaRail !== false)
const contentWide = computed(() => props.config.document?.wide === true)
// Dynamic schema loading must not cover a new form with the full-page pending
// overlay. Show the record as soon as GET returns; type fields fill in after.
const documentPending = computed(() =>
  !isCreate.value && pending.value,
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
    await exportRunner.run({
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

async function refreshDocument() {
  await load()
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
    :list-to="openedFromTopics ? '/meetings/topics' : config.routeBase"
    :is-create="isCreate"
    :can-comment="canCommentDocument"
    :can-export="canExportDocument"
    :comments="comments"
    :activity="activity"
    :attachments="attachments"
    :attachment-upload-endpoint="attachmentUploadEndpoint"
    :attachment-upload-version="() => concurrencyVersion(model)"
    @attached="onAttachmentAttached"
    :comment-body="commentBody"
    :submitting-comment="submittingComment"
    :updating-comment-id="updatingCommentId"
    :deleting-comment-id="deletingCommentId"
    :has-more-feed="hasMoreFeed"
    :loading-more-feed="loadingMoreFeed"
    :current-user="currentUser"
    :meta-title="title"
    :meta-subtitle="codeOrRef"
    :meta-owner="(model.owner as any) || null"
    :meta-assignee="(model.assignee as any) || null"
    :meta-tags="(model.tags as string[]) || []"
    :meta-created-at="model.createdAt ? String(model.createdAt) : undefined"
    :meta-updated-at="model.updatedAt ? String(model.updatedAt) : undefined"
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
    @export="exportDocument"
  />
</template>
