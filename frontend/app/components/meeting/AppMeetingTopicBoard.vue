<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import {
  MEETING_BOARD_UNASSIGNED,
  useMeetingTopicBoard,
} from '~/composables/meeting/useMeetingTopicBoard'
import { consumeListStale } from '~/utils/workspace-list-stale'
import { permissionForAction } from '~/utils/role/access'
import { useConfirm } from '~/composables/common/useConfirm'

const {
  pending,
  error,
  topics,
  meetings,
  topicSearch,
  meetingSearch,
  meetingDateStart,
  meetingDateEnd,
  selectedTopicId,
  selectedTopic,
  isAllMeetings,
  isUnassigned,
  isPoolView,
  filteredTopics,
  filteredMeetings,
  allMeetingCount,
  unassignedMeetingCount,
  topicMeetingCounts,
  hasMoreTopics,
  hasMoreMeetings,
  loadingMoreTopics,
  loadingMoreMeetings,
  draggingMeetingId,
  dropTopicId,
  refresh,
  loadMoreTopics,
  loadMoreMeetings,
  selectTopic,
  assignMeetingToTopic,
  reorderMeeting,
  deleteTopic,
  deleteMeeting,
  openTopic,
  openMeeting,
  openCreateTopic,
  openCreateMeeting,
} = useMeetingTopicBoard()

const { t } = useI18n()
const toast = useToast()
const { confirm } = useConfirm()
const auth = useAuthStore()

const notesOpen = ref(false)
const notesMeetingId = ref<string | null>(null)
const topicPanelOpen = ref(false)
const topicListCollapsed = useState('meeting-topic-left-collapsed', () => false)
const isSmallScreen = useMediaQuery('(max-width: 1023px)')
/** Desktop only: icon rail when collapsed. Small screens never use an icon rail. */
const topicPanelCollapsed = computed(() =>
  isSmallScreen.value ? false : topicListCollapsed.value,
)

function toggleTopicPanel() {
  if (isSmallScreen.value) {
    topicPanelOpen.value = !topicPanelOpen.value
    return
  }
  topicListCollapsed.value = !topicListCollapsed.value
}

const canCreateTopic = computed(() =>
  auth.canAccessPage(permissionForAction('meetings.topics.view', 'create')),
)
const canCreateMeeting = computed(() =>
  auth.canAccessPage(permissionForAction('meetings.history.view', 'create')),
)
const canAssignMeeting = computed(() =>
  auth.canAccessPage(permissionForAction('meetings.history.view', 'assign')),
)
const canEditMeeting = computed(() =>
  auth.canAccessPage(permissionForAction('meetings.history.view', 'edit')),
)
const canDeleteTopic = computed(() =>
  auth.canAccessPage(permissionForAction('meetings.topics.view', 'delete')),
)
const canDeleteMeeting = computed(() =>
  auth.canAccessPage(permissionForAction('meetings.history.view', 'delete')),
)

/** Add Topic always (when allowed); Add Meeting on All / Unassigned pool views. */
const createButtons = computed(() => {
  const buttons: Array<{ labelKey: string, icon?: string }> = []
  if (canCreateTopic.value) {
    buttons.push({ labelKey: 'docetra.meetingBoard.createTopic', icon: 'i-lucide-messages-square' })
  }
  if (canCreateMeeting.value && isPoolView.value) {
    buttons.push({ labelKey: 'docetra.meetingBoard.createMeeting', icon: 'i-lucide-calendar-plus' })
  }
  return buttons
})

const meetingsPanelTitle = computed(() => {
  if (selectedTopic.value) return selectedTopic.value.title
  if (isUnassigned.value) return t('docetra.meetingBoard.unassigned')
  return t('docetra.meetingBoard.allMeetings')
})

function onCreateButton(index: number) {
  const button = createButtons.value[index]
  if (!button) return
  if (button.labelKey === 'docetra.meetingBoard.createTopic') openCreateTopic()
  else openCreateMeeting()
}

function selectTopicFromPanel(topicId: string | null) {
  selectTopic(topicId)
  if (isSmallScreen.value) topicPanelOpen.value = false
}

onMounted(() => {
  // Always reload when entering the board (including return from /new).
  consumeListStale('meetingTopics', 'meetingHistory')
  void refresh()
})

onActivated(() => {
  if (consumeListStale('meetingTopics', 'meetingHistory')) void refresh()
})

function openMeetingNotes(id: string) {
  if (!canEditMeeting.value) return
  notesMeetingId.value = id
  notesOpen.value = true
}

function onNotesSaved(meeting: { id: string, notes?: string, attachmentCount?: number }) {
  const target = meetings.value.find(m => m.id === meeting.id)
  if (!target) return
  target.notes = meeting.notes
  target.attachmentCount = meeting.attachmentCount
}

function onNotesClosed() {
  notesMeetingId.value = null
}

function onMeetingDragStart(id: string) {
  if (!canAssignMeeting.value) return
  draggingMeetingId.value = id
}

function onMeetingDragEnd() {
  draggingMeetingId.value = null
  dropTopicId.value = null
}

function onTopicDrop(topicId: string, meetingId: string) {
  if (!canAssignMeeting.value) return
  dropTopicId.value = null
  assignMeetingToTopic(meetingId, topicId)
}

function onUnassignedDrop(event: DragEvent) {
  if (!canAssignMeeting.value) return
  event.preventDefault()
  dropTopicId.value = null
  if (!draggingMeetingId.value) return
  assignMeetingToTopic(draggingMeetingId.value, null)
}

async function onReorderBefore(beforeId: string | null) {
  if (!canAssignMeeting.value || !draggingMeetingId.value || isPoolView.value) return
  await reorderMeeting(draggingMeetingId.value, beforeId)
  draggingMeetingId.value = null
}

function onMeetingsPanelDrop(event: DragEvent) {
  event.preventDefault()
  if (isPoolView.value || !draggingMeetingId.value) return
  onReorderBefore(null)
}

async function onDeleteTopic(id: string) {
  if (!canDeleteTopic.value) return
  const accepted = await confirm({ kind: 'delete', count: 1 })
  if (!accepted) return
  try {
    await deleteTopic(id)
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.actions.deleteFailed'), color: 'error' })
  }
}

async function onDeleteMeeting(id: string) {
  if (!canDeleteMeeting.value) return
  const accepted = await confirm({ kind: 'delete', count: 1 })
  if (!accepted) return
  try {
    await deleteMeeting(id)
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.actions.deleteFailed'), color: 'error' })
  }
}
</script>

<template>
  <WorkspaceAppWorkspacePage
    title-key="docetra.pages.meetingTopic"
    description-key="docetra.descriptions.meetingTopic"
    icon="i-lucide-messages-square"
    :create-buttons="createButtons.length ? createButtons : undefined"
    :refreshing="pending"
    @create-button="onCreateButton"
    @refresh="refresh"
  >
    <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default">
      <div
        v-if="pending && !topics.length"
        class="absolute inset-0 z-10 flex items-center justify-center bg-default/50"
      >
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <UAlert
        v-if="error"
        class="m-3"
        color="error"
        :title="error"
        :actions="[{ label: $t('docetra.actions.retry'), onClick: refresh }]"
      />

      <div class="relative flex min-h-0 flex-1 overflow-hidden">
        <button
          v-if="isSmallScreen && topicPanelOpen"
          type="button"
          class="absolute inset-0 z-20 bg-black/25 lg:hidden"
          :aria-label="$t('actions.close')"
          @click="topicPanelOpen = false"
        />

        <!-- 1 col: topics — overlay drawer on small screens (no icon rail); collapsible rail on lg+ -->
        <aside
          class="flex min-h-0 shrink-0 flex-col overflow-hidden border-e border-default bg-default transition-[width] duration-200 lg:static lg:z-auto lg:shadow-none"
          :class="isSmallScreen
            ? (topicPanelOpen
                ? 'absolute inset-y-0 inset-s-0 z-30 w-[min(22rem,calc(100%-3rem))] shadow-xl'
                : 'hidden')
            : ''"
          :style="isSmallScreen
            ? undefined
            : { width: topicPanelCollapsed ? '3.5rem' : 'min(22rem, calc(100% - 3rem))' }"
        >
          <div
            class="shrink-0 border-b border-default"
            :class="topicPanelCollapsed ? 'space-y-1.5 px-1.5 py-3.5' : 'space-y-2 px-3 py-2.5'"
          >
            <div v-if="!topicPanelCollapsed" class="flex items-center justify-between gap-2">
              <h2 class="min-w-0 truncate text-sm font-semibold text-highlighted">
                {{ $t('docetra.pages.meetingTopic') }}
              </h2>
              <UButton
                icon="i-lucide-panel-left-close"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                class="shrink-0 lg:hidden"
                :aria-label="$t('actions.close')"
                @click="topicPanelOpen = false"
              />
            </div>
            <div v-else class="flex justify-center">
              <UIcon name="i-lucide-messages-square" class="size-4 text-muted" />
            </div>
            <CommonAppLiveSearch
              v-if="!topicPanelCollapsed"
              v-model="topicSearch"
              class="w-full"
              :placeholder="$t('docetra.meetingBoard.searchTopics')"
            />
            <button
              :data-meeting-topic-drop="MEETING_BOARD_UNASSIGNED"
              type="button"
              class="w-full transition"
              :class="topicPanelCollapsed
                ? [
                    'flex justify-center rounded-md p-2',
                    isAllMeetings
                      ? 'bg-primary/10 text-primary ring-1 ring-primary/30'
                      : 'text-muted hover:bg-elevated hover:text-highlighted',
                  ]
                : [
                    'rounded-lg border px-3 py-2 text-left text-sm',
                    isAllMeetings
                      ? 'border-primary bg-primary/5 font-medium text-highlighted ring-1 ring-primary/25'
                      : 'border-default text-muted hover:border-primary/30',
                  ]"
              :aria-label="$t('docetra.meetingBoard.allMeetings')"
              :title="topicPanelCollapsed ? $t('docetra.meetingBoard.allMeetings') : undefined"
              @click="selectTopicFromPanel(null)"
            >
              <UIcon v-if="topicPanelCollapsed" name="i-lucide-layout-grid" class="size-4" />
              <template v-else>
                {{ $t('docetra.meetingBoard.allMeetings') }}
                <span class="ml-1 tabular-nums text-xs">({{ allMeetingCount }})</span>
              </template>
            </button>
            <button
              type="button"
              class="w-full transition"
              :class="[
                topicPanelCollapsed
                  ? 'flex justify-center rounded-md p-2'
                  : 'rounded-lg border px-3 py-2 text-left text-sm',
                isUnassigned
                  ? (topicPanelCollapsed
                      ? 'bg-primary/10 text-primary ring-1 ring-primary/30'
                      : 'border-primary bg-primary/5 font-medium text-highlighted ring-1 ring-primary/25')
                  : (topicPanelCollapsed
                      ? 'text-muted hover:bg-elevated hover:text-highlighted'
                      : 'border-default text-muted hover:border-primary/30'),
                dropTopicId === MEETING_BOARD_UNASSIGNED ? 'ring-2 ring-primary/40' : '',
              ]"
              :aria-label="$t('docetra.meetingBoard.unassigned')"
              :title="topicPanelCollapsed ? $t('docetra.meetingBoard.unassigned') : undefined"
              @click="selectTopicFromPanel(MEETING_BOARD_UNASSIGNED)"
              @dragover.prevent="dropTopicId = MEETING_BOARD_UNASSIGNED"
              @dragleave="dropTopicId = dropTopicId === MEETING_BOARD_UNASSIGNED ? null : dropTopicId"
              @drop="onUnassignedDrop"
            >
              <UIcon v-if="topicPanelCollapsed" name="i-lucide-circle-dashed" class="size-4" />
              <template v-else>
                {{ $t('docetra.meetingBoard.unassigned') }}
                <span class="ml-1 tabular-nums text-xs">({{ unassignedMeetingCount }})</span>
              </template>
            </button>
          </div>

          <div
            class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden"
            :class="topicPanelCollapsed ? 'space-y-1 p-1.5' : 'space-y-2 p-3'"
          >
            <MeetingAppMeetingTopicSideCard
              v-for="topic in filteredTopics"
              :key="topic.id"
              :topic="topic"
              :meeting-count="topicMeetingCounts.get(topic.id) || 0"
              :selected="selectedTopicId === topic.id"
              :collapsed="topicPanelCollapsed"
              :drop-active="dropTopicId === topic.id"
              :can-drop="canAssignMeeting"
              :can-delete="canDeleteTopic"
              @select="selectTopicFromPanel(topic.id)"
              @open="openTopic(topic.id)"
              @drag-over="dropTopicId = topic.id"
              @drag-leave="dropTopicId = dropTopicId === topic.id ? null : dropTopicId"
              @drop-meeting="(id) => onTopicDrop(topic.id, id)"
              @delete="onDeleteTopic(topic.id)"
            />

            <UButton
              v-if="hasMoreTopics && !topicPanelCollapsed"
              block
              color="neutral"
              variant="soft"
              icon="i-lucide-chevrons-down"
              :loading="loadingMoreTopics"
              @click="loadMoreTopics"
            >
              {{ $t('docetra.actions.loadMore') }}
            </UButton>

            <p v-if="!filteredTopics.length && !pending && !topicPanelCollapsed" class="py-8 text-center text-xs text-muted">
              {{ $t('docetra.states.empty') }}
            </p>
          </div>
        </aside>

        <!-- 3 cols: meetings -->
        <section class="flex min-h-0 min-w-0 flex-1 flex-col">
          <div class="flex shrink-0 items-center gap-2 border-b border-default px-3 py-2.5">
            <UButton
              :icon="topicPanelOpen ? 'i-lucide-panel-left-close' : 'i-lucide-panel-left-open'"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="shrink-0 lg:hidden"
              :aria-label="$t('docetra.pages.meetingTopic')"
              :aria-expanded="topicPanelOpen"
              @click="toggleTopicPanel"
            />
            <UButton
              :icon="topicPanelCollapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="hidden shrink-0 lg:inline-flex"
              :aria-label="topicPanelCollapsed
                ? $t('docetra.meetingBoard.expandTopics')
                : $t('docetra.meetingBoard.collapseTopics')"
              :aria-expanded="!topicPanelCollapsed"
              @click="toggleTopicPanel"
            />
            <h2 class="hidden min-w-0 max-w-40 truncate text-sm font-semibold text-highlighted sm:block">
              {{ meetingsPanelTitle }}
            </h2>
            <CommonAppLiveSearch
              v-model="meetingSearch"
              class="min-w-0 flex-1 w-full max-w-75"
              :placeholder="$t('docetra.meetingBoard.searchMeetings')"
            />
            <CommonAppDateRangeFilter
              v-model:start="meetingDateStart"
              v-model:end="meetingDateEnd"
              class="ms-auto shrink-0"
              size="sm"
            />
          </div>

          <div
            class="min-h-0 flex-1 overflow-y-auto p-3"
            @dragover.prevent
            @drop="onMeetingsPanelDrop"
          >
            <div
              class="grid items-stretch gap-2"
              style="grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));"
            >
              <MeetingAppMeetingBoardCard
                v-for="meeting in filteredMeetings"
                :key="meeting.id"
                :meeting="meeting"
                :topics="topics"
                :dragging="draggingMeetingId === meeting.id"
                :show-topic="isPoolView"
                :can-assign="canAssignMeeting"
                :can-edit-notes="canEditMeeting"
                :can-delete="canDeleteMeeting"
                @open="openMeeting(meeting.id)"
                @open-notes="openMeetingNotes(meeting.id)"
                @drag-start="onMeetingDragStart"
                @drag-end="onMeetingDragEnd"
                @assign="(topicId) => canAssignMeeting && assignMeetingToTopic(meeting.id, topicId)"
                @reorder-before="onReorderBefore"
                @delete="onDeleteMeeting(meeting.id)"
              />
            </div>

            <div v-if="hasMoreMeetings" class="flex justify-center py-4">
              <UButton
                color="neutral"
                variant="soft"
                icon="i-lucide-chevrons-down"
                :loading="loadingMoreMeetings"
                @click="loadMoreMeetings"
              >
                {{ $t('docetra.actions.loadMore') }}
              </UButton>
            </div>

            <div
              v-if="!filteredMeetings.length && !pending"
              class="flex flex-col items-center justify-center gap-2 py-16 text-center"
            >
              <UIcon name="i-lucide-calendar-off" class="size-8 text-muted" />
              <p class="text-sm text-muted">{{ $t('docetra.meetingBoard.emptyMeetings') }}</p>
            </div>
          </div>
        </section>
      </div>
    </div>

    <MeetingAppMeetingNotesDialog
      v-if="notesOpen && notesMeetingId"
      v-model:open="notesOpen"
      :meeting-id="notesMeetingId"
      @saved="onNotesSaved"
      @closed="onNotesClosed"
    />
  </WorkspaceAppWorkspacePage>
</template>
