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

const canCreateTopic = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_topic.view', 'create')),
)
const canCreateMeeting = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_history.view', 'create')),
)
const canAssignMeeting = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_history.view', 'assign')),
)
const canEditMeeting = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_history.view', 'edit')),
)
const canDeleteTopic = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_topic.view', 'delete')),
)
const canDeleteMeeting = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_history.view', 'delete')),
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
    <WorkspaceAppBoardShell
      v-model:collapsed="topicListCollapsed"
      v-model:mobile-open="topicPanelOpen"
      v-model:rail-search="topicSearch"
      v-model:header-search="meetingSearch"
      v-model:date-start="meetingDateStart"
      v-model:date-end="meetingDateEnd"
      rail-title-key="docetra.pages.meetingTopic"
      rail-icon="i-lucide-messages-square"
      expand-label-key="docetra.meetingBoard.expandTopics"
      collapse-label-key="docetra.meetingBoard.collapseTopics"
      rail-search-placeholder-key="docetra.meetingBoard.searchTopics"
      header-search-placeholder-key="docetra.meetingBoard.searchMeetings"
      :header-title="meetingsPanelTitle"
      :pending="pending"
      :show-pending-overlay="pending && !topics.length"
      :error="error || undefined"
      @retry="refresh"
    >
      <template #rail-pills>
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
      </template>

      <template #rail-items>
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
      </template>

      <div
        class="min-h-0 flex-1 overflow-y-auto p-3"
        @dragover.prevent
        @drop="onMeetingsPanelDrop"
      >
        <div
          class="grid items-stretch gap-2"
          style="grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));"
        >
          <RecordAppRecordBoardCard
            v-for="meeting in filteredMeetings"
            :key="meeting.id"
            :meeting="meeting"
            :topics="topics"
            :title="meeting.title"
            entity-key="meetingHistory"
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
    </WorkspaceAppBoardShell>

    <MeetingAppMeetingNotesDialog
      v-if="notesOpen && notesMeetingId"
      v-model:open="notesOpen"
      :meeting-id="notesMeetingId"
      @saved="onNotesSaved"
      @closed="onNotesClosed"
    />
  </WorkspaceAppWorkspacePage>
</template>
