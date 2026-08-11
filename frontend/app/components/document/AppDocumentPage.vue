<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type {
  ActivityEvent,
  AttachmentMeta,
  DocumentTabSchema,
  EntityComment,
  PersonSummary,
} from '~/types/docetra/common'
import { useConfirm } from '~/composables/common/useConfirm'
import type { ExportRequest } from '~/types/docetra/export'

const props = withDefaults(defineProps<{
  tabs: DocumentTabSchema[]
  activeTab: string
  fieldValue: (key: string) => unknown
  setFieldValue: (key: string, value: unknown) => void | Promise<void>
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
  canNavigatePrevious?: boolean
  canNavigateNext?: boolean
  loadingListNavigation?: boolean
  listNavigationDirection?: 'previous' | 'next' | null
  listTo?: string
  isCreate?: boolean
  /** Force the wider document content shell (matches App Config settings width). */
  contentWide?: boolean
  canComment?: boolean
  comments?: EntityComment[]
  activity?: ActivityEvent[]
  attachments?: AttachmentMeta[]
  commentBody?: string
  submittingComment?: boolean
  updatingCommentId?: string | null
  deletingCommentId?: string | null
  hasMoreFeed?: boolean
  loadingMoreFeed?: boolean
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
  metaFavorite?: boolean
  togglingFavorite?: boolean
  moreItems?: DropdownMenuItem[][]
  exporting?: boolean
  canExport?: boolean
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
  canNavigatePrevious: false,
  canNavigateNext: false,
  loadingListNavigation: false,
  listNavigationDirection: null,
  isCreate: false,
  contentWide: false,
  canComment: true,
  comments: () => [],
  activity: () => [],
  attachments: () => [],
  commentBody: '',
  submittingComment: false,
  updatingCommentId: null,
  deletingCommentId: null,
  hasMoreFeed: false,
  loadingMoreFeed: false,
  metaTags: () => [],
  exporting: false,
  canExport: true,
})

const emit = defineEmits<{
  'update:activeTab': [string]
  'update:commentBody': [string]
  'update:attachments': [AttachmentMeta[]]
  save: []
  refresh: []
  submitComment: []
  updateComment: [id: string, body: string]
  deleteComment: [id: string]
  loadMoreFeed: []
  navigatePrevious: []
  navigateNext: []
  toggleFavorite: []
  export: [request: ExportRequest]
}>()

const { t } = useI18n()

const exportFields = computed(() => {
  if (!props.canExport) return []
  const fields = props.tabs.flatMap(tab =>
    tab.sections.flatMap(section =>
      section.fields
        .filter(field => field.type !== 'secret' && field.type !== 'alert')
        .map(field => ({
          label: field.label || t(field.labelKey),
          value: field.key,
        })),
    ),
  )
  return [...new Map(fields.map(field => [field.value, field])).values()]
})

const localAttachments = computed({
  get: () => props.attachments || [],
  set: (value: AttachmentMeta[]) => emit('update:attachments', value),
})

const showForm = computed(() =>
  !props.notFound && !props.error && (!props.pending || props.tabs.length > 0),
)

const { confirm } = useConfirm()

const scrollEl = ref<HTMLElement | null>(null)
const showScrollTop = ref(false)
const metaRailOpen = ref(false)

function onFormScroll() {
  showScrollTop.value = (scrollEl.value?.scrollTop ?? 0) > 240
}

function scrollToTop() {
  scrollEl.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

function selectTab(value: string) {
  emit('update:activeTab', value)
  scrollEl.value?.scrollTo({ top: 0 })
}

async function onSaveClick() {
  const ok = await confirm({
    kind: props.isCreate ? 'submit' : 'save',
  })
  if (ok) emit('save')
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden bg-default">
    <LayoutAppHeaderPageActions
      :can-create="false"
      :refreshing="pending"
      :more-items="moreItems"
      :export-fields="exportFields"
      :exporting="exporting"
      @refresh="emit('refresh')"
      @export="emit('export', $event)"
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
            :loading="listNavigationDirection === 'previous'"
            :disabled="isCreate || !canNavigatePrevious || loadingListNavigation || Boolean(listNavigationDirection)"
            :aria-label="t('docetra.document.previous')"
            @click="emit('navigatePrevious')"
          />
          <UButton
            v-if="showListNav"
            color="neutral"
            variant="soft"
            icon="i-lucide-chevron-right"
            square
            class="rounded-md"
            :loading="listNavigationDirection === 'next'"
            :disabled="isCreate || !canNavigateNext || loadingListNavigation || Boolean(listNavigationDirection)"
            :aria-label="t('docetra.document.next')"
            @click="emit('navigateNext')"
          />
        </slot>
      </template>

      <slot name="actions" />

      <UButton
        v-if="showMetaRail && !notFound && !error && showForm"
        icon="i-lucide-menu"
        color="neutral"
        variant="soft"
        square
        class="rounded-md lg:hidden"
        :aria-label="t('docetra.tabs.details')"
        :aria-expanded="metaRailOpen"
        @click="metaRailOpen = !metaRailOpen"
      />

      <UButton
        v-if="showSave && canSave && !readOnly"
        :loading="saving"
        icon="i-lucide-save"
        :label="saveLabel || t('actions.save')"
        class="rounded-md"
        @click="onSaveClick"
      />
    </LayoutAppHeaderPageActions>

    <div class="relative flex min-h-0 w-full min-w-0 flex-1 overflow-hidden p-0">
      <div
        v-if="pending"
        class="absolute inset-0 z-10 flex items-center justify-center bg-default/50 backdrop-blur-[1px]"
      >
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <div class="relative flex min-h-0 w-full min-w-0 flex-1 overflow-hidden bg-default">
        <button
          v-if="metaRailOpen"
          type="button"
          class="absolute inset-0 z-20 bg-black/25 lg:hidden"
          :aria-label="t('actions.close')"
          @click="metaRailOpen = false"
        />

        <div class="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <DocumentAppDocumentTabBar
            v-if="showForm && !notFound && !error"
            :tabs="tabs"
            :active-tab="activeTab"
            @update:active-tab="selectTab"
          />

          <div
            ref="scrollEl"
            class="min-h-0 min-w-0 flex-1 overflow-auto"
            @scroll.passive="onFormScroll"
          >
            <UAlert
              v-if="notFound"
              class="mx-auto mt-6 w-full px-4 sm:px-6 lg:px-10"
              :class="contentWide
                ? 'max-w-4xl lg:max-w-5xl xl:max-w-6xl'
                : 'max-w-xl sm:max-w-2xl lg:max-w-3xl'"
              color="error"
              :title="t('docetra.states.notFound')"
            />
            <UAlert
              v-else-if="error"
              class="mx-auto mt-6 w-full px-4 sm:px-6 lg:px-10"
              :class="contentWide
                ? 'max-w-4xl lg:max-w-5xl xl:max-w-6xl'
                : 'max-w-xl sm:max-w-2xl lg:max-w-3xl'"
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
                    :wide="contentWide"
                  />

                  <DocumentAppDocumentContentShell
                    v-if="showComments && !isCreate"
                    :wide="contentWide"
                  >
                    <DocumentAppCommentsActivity
                      :comments="comments"
                      :activity="activity"
                      :comment-body="commentBody"
                      :submitting="submittingComment"
                      :updating-comment-id="updatingCommentId"
                      :deleting-comment-id="deletingCommentId"
                      :has-more="hasMoreFeed"
                      :loading-more="loadingMoreFeed"
                      :can-comment="canComment"
                      :current-user="currentUser"
                      @update:comment-body="emit('update:commentBody', $event)"
                      @submit="emit('submitComment')"
                      @update-comment="emit('updateComment', $event.id, $event.body)"
                      @delete-comment="emit('deleteComment', $event)"
                      @load-more="emit('loadMoreFeed')"
                    />
                  </DocumentAppDocumentContentShell>

                  <DocumentAppDocumentContentShell
                    v-if="$slots['after-form']"
                    :wide="contentWide"
                    class="space-y-3 pb-6"
                  >
                    <slot name="after-form" />
                  </DocumentAppDocumentContentShell>
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

          <UButton
            v-show="showScrollTop && showForm"
            icon="i-lucide-chevron-up"
            color="neutral"
            variant="soft"
            size="sm"
            square
            class="absolute bottom-4 right-4 z-20 border border-default shadow-sm"
            :aria-label="t('docetra.document.scrollToTop')"
            @click="scrollToTop"
          />
        </div>

        <aside
          v-if="showMetaRail && !notFound && !error && showForm"
          class="absolute inset-y-0 end-0 z-30 w-[min(22rem,calc(100%-3rem))] bg-default shadow-xl transition-transform duration-200 lg:static lg:z-auto lg:w-64 lg:translate-x-0 lg:shadow-none xl:w-72"
          :class="metaRailOpen ? 'translate-x-0' : 'translate-x-full rtl:-translate-x-full'"
        >
          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            size="sm"
            square
            class="absolute end-2 top-2 z-10 lg:hidden"
            :aria-label="t('actions.close')"
            @click="metaRailOpen = false"
          />
          <DocumentAppDocumentMetaRail
            class="h-full min-h-0 overflow-y-auto"
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
            :is-favorite="metaFavorite"
            :toggling-favorite="togglingFavorite"
            :favorite-enabled="!isCreate"
            @update:tags="setFieldValue('tags', $event)"
            @update:attachments="localAttachments = $event"
            @update:assignees="setFieldValue('assignee', $event[0] || null)"
            @toggle-favorite="emit('toggleFavorite')"
          />
        </aside>
      </div>
    </div>
  </div>
</template>
