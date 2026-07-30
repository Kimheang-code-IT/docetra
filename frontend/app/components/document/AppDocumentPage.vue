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
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden bg-default">
    <LayoutAppHeaderPageActions
      :can-create="!config.readOnly"
      :create-label="$t('actions.save')"
      create-icon="i-lucide-save"
      :refreshing="pending"
      :more-items="moreItems"
      @refresh="load"
      @create="save"
    >
      <template #leading>
        <UButton
          color="neutral"
          variant="soft"
          icon="i-lucide-list"
          :to="config.routeBase"
          :label="$t('docetra.document.listView')"
          class="hidden rounded-md sm:inline-flex"
        />
        <UButton
          color="neutral"
          variant="soft"
          icon="i-lucide-chevron-left"
          square
          class="rounded-md"
          :disabled="isCreate"
          :aria-label="$t('docetra.document.previous')"
        />
        <UButton
          color="neutral"
          variant="soft"
          icon="i-lucide-chevron-right"
          square
          class="rounded-md"
          :disabled="isCreate"
          :aria-label="$t('docetra.document.next')"
        />
      </template>
    </LayoutAppHeaderPageActions>

    <div class="relative flex min-h-0 w-full min-w-0 flex-1 overflow-hidden p-0">
      <div
        v-if="pending"
        class="absolute inset-0 z-10 flex items-center justify-center bg-default/50 backdrop-blur-[1px]"
      >
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <div class="flex min-h-0 w-full min-w-0 flex-1 overflow-hidden bg-default">
        <div class="min-h-0 min-w-0 flex-1 overflow-auto">
          <UAlert
            v-if="notFound"
            class="mx-auto mt-6 w-full max-w-3xl xl:max-w-4xl"
            color="error"
            :title="$t('docetra.states.notFound')"
          />
          <UAlert
            v-else-if="error"
            class="mx-auto mt-6 w-full max-w-3xl xl:max-w-4xl"
            color="error"
            :title="error"
          />

          <template v-else-if="!pending || Object.keys(model).length">
            <DocumentAppDocumentForm
              :tabs="config.tabs"
              v-model:active-tab="activeTab"
              :field-value="fieldValue"
              :set-field-value="setFieldValue"
              :read-only="config.readOnly"
            />

            <div class="mx-auto w-full max-w-3xl px-6 xl:max-w-4xl">
              <DocumentAppCommentsActivity
                v-if="!isCreate"
                :comments="comments"
                :activity="activity"
                :comment-body="commentBody"
                :submitting="submittingComment"
                :can-comment="config.canComment !== false"
                :current-user="{ id: 'current', name: auth.user?.name || 'You', email: auth.user?.email }"
                @update:comment-body="commentBody = $event"
                @submit="submitComment"
              />
            </div>
          </template>
        </div>

        <DocumentAppDocumentMetaRail
          v-if="!notFound && !error && (!pending || Object.keys(model).length)"
          class="hidden min-h-0 overflow-y-auto lg:flex"
          :title="title"
          :subtitle="codeOrRef"
          :status="statusLabel"
          :stage="model.stage ? String(model.stage) : undefined"
          :owner="model.owner as any"
          :assignee="model.assignee as any"
          :attachments="attachments"
          :tags="(model.tags as string[]) || []"
          :created-at="model.createdAt ? String(model.createdAt) : undefined"
          :updated-at="model.updatedAt ? String(model.updatedAt) : undefined"
          :read-only="config.readOnly"
          @update:tags="setFieldValue('tags', $event)"
          @update:attachments="attachments = $event"
          @update:assignees="setFieldValue('assignee', $event[0] || null)"
        />
      </div>
    </div>
  </div>
</template>
