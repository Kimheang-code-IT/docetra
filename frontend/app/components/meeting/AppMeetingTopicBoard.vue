<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import {
  MEETING_BOARD_UNASSIGNED,
  useMeetingTopicBoard,
} from '~/composables/meeting/useMeetingTopicBoard'

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
  draggingMeetingId,
  dropTopicId,
  refresh,
  selectTopic,
  assignMeetingToTopic,
  reorderMeeting,
  openTopic,
  openMeeting,
  openCreateTopic,
  openCreateMeeting,
} = useMeetingTopicBoard()

const { t } = useI18n()

const notesOpen = ref(false)
const notesMeetingId = ref<string | null>(null)
const topicPanelOpen = ref(false)
const isSmallScreen = useMediaQuery('(max-width: 1023px)')
const topicPanelCollapsed = computed(() => isSmallScreen.value && !topicPanelOpen.value)

/** Add Topic always; Add Meeting on All / Unassigned pool views. */
const createButtons = computed(() => {
  const buttons = [
    { labelKey: 'docetra.meetingBoard.createTopic', icon: 'i-lucide-messages-square' },
  ]
  if (isPoolView.value) {
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
  if (index === 0) openCreateTopic()
  else openCreateMeeting()
}

function selectTopicFromPanel(topicId: string | null) {
  selectTopic(topicId)
}

onMounted(() => {
  refresh()
})

function openMeetingNotes(id: string) {
  notesMeetingId.value = id
  notesOpen.value = true
}

function onNotesSaved(meeting: { id: string, notes?: string, attachmentCount?: number }) {
  const target = meetings.value.find(m => m.id === meeting.id)
  if (!target) return
  target.notes = meeting.notes
  target.attachmentCount = meeting.attachmentCount
}

function onMeetingDragStart(id: string) {
  draggingMeetingId.value = id
}

function onMeetingDragEnd() {
  draggingMeetingId.value = null
  dropTopicId.value = null
}

function onTopicDrop(topicId: string, meetingId: string) {
  dropTopicId.value = null
  assignMeetingToTopic(meetingId, topicId)
}

function onUnassignedDrop(event: DragEvent) {
  event.preventDefault()
  dropTopicId.value = null
  if (!draggingMeetingId.value) return
  assignMeetingToTopic(draggingMeetingId.value, null)
}

async function onReorderBefore(beforeId: string | null) {
  if (!draggingMeetingId.value || isPoolView.value) return
  await reorderMeeting(draggingMeetingId.value, beforeId)
  draggingMeetingId.value = null
}

function onMeetingsPanelDrop(event: DragEvent) {
  event.preventDefault()
  if (isPoolView.value || !draggingMeetingId.value) return
  onReorderBefore(null)
}
</script>

<template>
  <WorkspaceAppWorkspacePage
    title-key="docetra.pages.meetingTopic"
    description-key="docetra.descriptions.meetingTopic"
    icon="i-lucide-messages-square"
    :create-buttons="createButtons"
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
        <!-- 1 col: topics -->
        <aside
          class="flex min-h-0 shrink-0 flex-col overflow-hidden border-e border-default bg-default transition-[width] duration-200"
          :style="{ width: topicPanelCollapsed ? '3.5rem' : (isSmallScreen ? 'min(22rem, calc(100% - 3rem))' : '25%') }"
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
                :aria-label="$t('docetra.pages.meetingTopic')"
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
              @select="selectTopicFromPanel(topic.id)"
              @open="openTopic(topic.id)"
              @drag-over="dropTopicId = topic.id"
              @drag-leave="dropTopicId = dropTopicId === topic.id ? null : dropTopicId"
              @drop-meeting="(id) => onTopicDrop(topic.id, id)"
            />

            <p v-if="!filteredTopics.length && !pending && !topicPanelCollapsed" class="py-8 text-center text-xs text-muted">
              {{ $t('docetra.states.empty') }}
            </p>
          </div>
        </aside>

        <!-- 3 cols: meetings -->
        <section class="flex min-h-0 min-w-0 flex-1 flex-col">
          <div class="flex shrink-0 items-center gap-2 border-b border-default px-3 py-2.5">
            <UButton
              :icon="topicPanelCollapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="shrink-0 lg:hidden"
              :aria-label="$t('docetra.pages.meetingTopic')"
              :aria-expanded="!topicPanelCollapsed"
              @click="topicPanelOpen = !topicPanelOpen"
            />
            <h2 class="hidden min-w-0 max-w-40 truncate text-sm font-semibold text-highlighted sm:block">
              {{ meetingsPanelTitle }}
            </h2>
            <CommonAppLiveSearch
              v-model="meetingSearch"
              class="min-w-0 w-full max-w-[18.75rem] flex-1"
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
                @open="openMeeting(meeting.id)"
                @open-notes="openMeetingNotes(meeting.id)"
                @drag-start="onMeetingDragStart"
                @drag-end="onMeetingDragEnd"
                @assign="(topicId) => assignMeetingToTopic(meeting.id, topicId)"
                @reorder-before="onReorderBefore"
              />
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
      v-if="notesOpen || notesMeetingId"
      v-model:open="notesOpen"
      :meeting-id="notesMeetingId"
      @saved="onNotesSaved"
    />
  </WorkspaceAppWorkspacePage>
</template>
