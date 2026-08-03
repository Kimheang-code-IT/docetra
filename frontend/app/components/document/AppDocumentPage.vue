<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type {
  ActivityEvent,
  AttachmentMeta,
  DocumentTabSchema,
  EntityComment,
  PersonSummary,
} from '~/types/docetra/common'

const props = withDefaults(defineProps<{
  tabs: DocumentTabSchema[]
  activeTab: string
  fieldValue: (key: string) => unknown
  setFieldValue: (key: string, value: unknown) => void
  pending?: boolean
  saving?: boolean
  error?: string | null
  notFound?: boolean
  readOnly?: boolean
  canSave?: boolean
  saveLabel?: string
  showSave?: boolean
  showComments?: boolean
  showMetaRail?: boolean
  showListNav?: boolean
  listTo?: string
  isCreate?: boolean
  canComment?: boolean
  comments?: EntityComment[]
  activity?: ActivityEvent[]
  attachments?: AttachmentMeta[]
  commentBody?: string
  submittingComment?: boolean
  currentUser?: { id: string, name: string, email?: string }
  metaTitle?: string
  metaSubtitle?: string
  metaStatus?: string
  metaStage?: string
  metaOwner?: PersonSummary | null
  metaAssignee?: PersonSummary | null
  metaTags?: string[]
  metaCreatedAt?: string
  metaUpdatedAt?: string
  moreItems?: DropdownMenuItem[][]
}>(), {
  pending: false,
  saving: false,
  error: null,
  notFound: false,
  readOnly: false,
  canSave: true,
  showSave: true,
  showComments: false,
  showMetaRail: false,
  showListNav: false,
  isCreate: false,
  canComment: true,
  comments: () => [],
  activity: () => [],
  attachments: () => [],
  commentBody: '',
  submittingComment: false,
  metaTags: () => [],
})

const emit = defineEmits<{
  'update:activeTab': [string]
  'update:commentBody': [string]
  'update:attachments': [AttachmentMeta[]]
  save: []
  refresh: []
  submitComment: []
}>()

const { t } = useI18n()

const localAttachments = computed({
  get: () => props.attachments || [],
  set: (value: AttachmentMeta[]) => emit('update:attachments', value),
})

const showForm = computed(() =>
  !props.notFound && !props.error && (!props.pending || props.tabs.length > 0),
)
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden bg-default">
    <LayoutAppHeaderPageActions
      :can-create="false"
      :refreshing="pending"
      :more-items="moreItems"
      @refresh="emit('refresh')"
    >
      <template v-if="showListNav || $slots.leading" #leading>
        <slot name="leading">
          <UButton
            v-if="showListNav && listTo"
            color="neutral"
            variant="soft"
            icon="i-lucide-list"
            :to="listTo"
            :label="t('docetra.document.listView')"
            class="hidden rounded-md sm:inline-flex"
          />
          <UButton
            v-if="showListNav"
            color="neutral"
            variant="soft"
            icon="i-lucide-chevron-left"
            square
            class="rounded-md"
            :disabled="isCreate"
            :aria-label="t('docetra.document.previous')"
          />
          <UButton
            v-if="showListNav"
            color="neutral"
            variant="soft"
            icon="i-lucide-chevron-right"
            square
            class="rounded-md"
            :disabled="isCreate"
            :aria-label="t('docetra.document.next')"
          />
        </slot>
      </template>

      <slot name="actions" />

      <UButton
        v-if="showSave && canSave && !readOnly"
        :loading="saving"
        icon="i-lucide-save"
        :label="saveLabel || t('actions.save')"
        class="rounded-md"
        @click="emit('save')"
      />
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
            :title="t('docetra.states.notFound')"
          />
          <UAlert
            v-else-if="error"
            class="mx-auto mt-6 w-full max-w-3xl xl:max-w-4xl"
            color="error"
            :title="error"
          />

          <template v-else-if="showForm">
            <slot name="before-form" />

            <div
              class="flex min-h-0 w-full"
              :class="$slots.aside && !showMetaRail ? 'flex-col xl:flex-row' : 'flex-col'"
            >
              <div class="min-w-0 flex-1">
                <DocumentAppDocumentForm
                  :tabs="tabs"
                  :active-tab="activeTab"
                  :field-value="fieldValue"
                  :set-field-value="setFieldValue"
                  :read-only="readOnly"
                  @update:active-tab="emit('update:activeTab', $event)"
                />

                <div
                  v-if="showComments && !isCreate"
                  class="mx-auto w-full max-w-3xl px-6 xl:max-w-4xl"
                >
                  <DocumentAppCommentsActivity
                    :comments="comments"
                    :activity="activity"
                    :comment-body="commentBody"
                    :submitting="submittingComment"
                    :can-comment="canComment"
                    :current-user="currentUser"
                    @update:comment-body="emit('update:commentBody', $event)"
                    @submit="emit('submitComment')"
                  />
                </div>

                <div
                  v-if="$slots['after-form']"
                  class="mx-auto w-full max-w-3xl space-y-3 px-4 pb-6 sm:px-6 xl:max-w-4xl"
                >
                  <slot name="after-form" />
                </div>
              </div>

              <aside
                v-if="$slots.aside && !showMetaRail"
                class="w-full shrink-0 border-t border-default px-4 py-6 sm:px-6 xl:w-80 xl:border-t-0 xl:border-l xl:overflow-y-auto"
              >
                <slot name="aside" />
              </aside>
            </div>
          </template>
        </div>

        <DocumentAppDocumentMetaRail
          v-if="showMetaRail && !notFound && !error && showForm"
          class="hidden min-h-0 overflow-y-auto lg:flex"
          :title="metaTitle"
          :subtitle="metaSubtitle"
          :status="metaStatus"
          :stage="metaStage"
          :owner="metaOwner || undefined"
          :assignee="metaAssignee || undefined"
          :attachments="localAttachments"
          :tags="metaTags"
          :created-at="metaCreatedAt"
          :updated-at="metaUpdatedAt"
          :read-only="readOnly"
          @update:tags="setFieldValue('tags', $event)"
          @update:attachments="localAttachments = $event"
          @update:assignees="setFieldValue('assignee', $event[0] || null)"
        />
      </div>
    </div>
  </div>
</template>
