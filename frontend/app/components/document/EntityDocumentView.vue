<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'
import { useDocumentPage } from '~/composables/workspace/useDocumentPage'
import { useAppHeader } from '~/composables/layout/useAppHeader'

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
  fieldValue,
  setFieldValue,
  load,
  save,
  submitComment,
} = useDocumentPage(props.config)

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
        label: isCreate.value ? t('docetra.document.newShort') : title.value,
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

useHead(() => ({
  title: `${title.value} · ${t('docetra.brand.name')}`,
}))

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
  id: 'current',
  name: auth.user?.name || 'You',
  email: auth.user?.email,
}))
</script>

<template>
  <DocumentAppDocumentPage
    :tabs="config.tabs"
    v-model:active-tab="activeTab"
    :field-value="fieldValue"
    :set-field-value="setFieldValue"
    :pending="pending"
    :saving="saving"
    :error="error"
    :not-found="notFound"
    :read-only="config.readOnly"
    :show-comments="!isCreate"
    :show-meta-rail="true"
    :show-list-nav="true"
    :list-to="config.routeBase"
    :is-create="isCreate"
    :can-comment="config.canComment !== false"
    :comments="comments"
    :activity="activity"
    :attachments="attachments"
    :comment-body="commentBody"
    :submitting-comment="submittingComment"
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
    :more-items="moreItems"
    @update:comment-body="commentBody = $event"
    @update:attachments="attachments = $event"
    @save="save"
    @refresh="load"
    @submit-comment="submitComment"
  />
</template>
