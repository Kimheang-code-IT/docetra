<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'
import { useDocumentPage } from '~/composables/workspace/useDocumentPage'
import { useRecordTypeDrivenTabs } from '~/composables/record/useRecordTypeDrivenTabs'
import { useAppHeader } from '~/composables/layout/useAppHeader'
import { usePageSeo } from '~/composables/usePageSeo'
import { getByPath, setByPath } from '~/utils/object-path'

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
  navigatePreviousRecord,
  navigateNextRecord,
  toggleFavorite,
} = useDocumentPage(props.config)

const { tabs: documentTabs } = useRecordTypeDrivenTabs({
  entityKey: props.config.key,
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
    const next = { ...model.value }
    setByPath(next, 'details', details)
    model.value = next
  },
  setStageIfEmpty: (stage) => {
    if (!getByPath(model.value, 'stage')) {
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

usePageSeo({
  title: () => title.value,
})

const moreItems = computed(() => [[
  {
    label: t('docetra.document.duplicate'),
    icon: 'i-lucide-copy',
    disabled: isCreate.value,
    onSelect: () => toast.add({ title: t('docetra.document.comingSoon'), color: 'neutral' }),
  },
  {
    label: t('docetra.document.print'),
    icon: 'i-lucide-printer',
    onSelect: () => toast.add({ title: t('docetra.document.comingSoon'), color: 'neutral' }),
  },
]])

const currentUser = computed(() => ({
  id: String(auth.user?.id || auth.user?.email || 'current'),
  name: auth.user?.name || 'You',
  email: auth.user?.email,
}))

const showMetaRail = computed(() => !['users', 'roles'].includes(props.config.key))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="documentTabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending"
    :saving="saving"
    :error="error"
    :not-found="notFound"
    :read-only="config.readOnly"
    :show-comments="!isCreate"
    :show-meta-rail="showMetaRail"
    :show-list-nav="true"
    :can-navigate-previous="Boolean(previousRecordId)"
    :can-navigate-next="Boolean(nextRecordId)"
    :loading-list-navigation="loadingRecordNavigation"
    :list-navigation-direction="recordNavigationDirection"
    :list-to="config.routeBase"
    :is-create="isCreate"
    :can-comment="config.canComment !== false"
    :comments="comments"
    :activity="activity"
    :attachments="attachments"
    :comment-body="commentBody"
    :submitting-comment="submittingComment"
    :updating-comment-id="updatingCommentId"
    :deleting-comment-id="deletingCommentId"
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
    @update:comment-body="commentBody = $event"
    @update:attachments="attachments = $event"
    @save="save"
    @refresh="load"
    @submit-comment="submitComment"
    @update-comment="updateComment"
    @delete-comment="deleteComment"
    @navigate-previous="navigatePreviousRecord"
    @navigate-next="navigateNextRecord"
    @toggle-favorite="toggleFavorite"
  />
</template>
