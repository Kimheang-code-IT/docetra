<script setup lang="ts">
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

const hasMeetingDateFilter = computed(() => Boolean(
  meetingDateStart.value.trim() || meetingDateEnd.value.trim(),
))

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
  topicPanelOpen.value = false
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
        <button
          v-if="topicPanelOpen"
          type="button"
          class="absolute inset-0 z-20 bg-black/25 lg:hidden"
          :aria-label="$t('actions.close')"
          @click="topicPanelOpen = false"
        />

        <!-- 1 col: topics -->
        <aside
          class="absolute inset-y-0 start-0 z-30 flex w-[min(22rem,calc(100%-3rem))] min-h-0 flex-col border-e border-default bg-default shadow-xl transition-transform duration-200 lg:static lg:z-auto lg:w-1/4 lg:translate-x-0 lg:shadow-none"
          :class="topicPanelOpen ? 'translate-x-0' : '-translate-x-full rtl:translate-x-full'"
        >
          <div class="shrink-0 space-y-2 border-b border-default px-3 py-2.5">
            <h2 class="text-sm font-semibold text-highlighted">
              {{ $t('docetra.pages.meetingTopic') }}
            </h2>
            <CommonAppLiveSearch
              v-model="topicSearch"
              class="w-full"
              :placeholder="$t('docetra.meetingBoard.searchTopics')"
            />
            <button
              type="button"
              class="w-full rounded-lg border px-3 py-2 text-left text-sm transition"
              :class="isAllMeetings
                ? 'border-primary bg-primary/5 font-medium text-highlighted ring-1 ring-primary/25'
                : 'border-default text-muted hover:border-primary/30'"
              @click="selectTopicFromPanel(null)"
            >
              {{ $t('docetra.meetingBoard.allMeetings') }}
              <span class="ml-1 tabular-nums text-xs">({{ allMeetingCount }})</span>
            </button>
            <button
              type="button"
              class="w-full rounded-lg border px-3 py-2 text-left text-sm transition"
              :class="[
                isUnassigned
                  ? 'border-primary bg-primary/5 font-medium text-highlighted ring-1 ring-primary/25'
                  : 'border-default text-muted hover:border-primary/30',
                dropTopicId === MEETING_BOARD_UNASSIGNED ? 'ring-2 ring-primary/40' : '',
              ]"
              @click="selectTopicFromPanel(MEETING_BOARD_UNASSIGNED)"
              @dragover.prevent="dropTopicId = MEETING_BOARD_UNASSIGNED"
              @dragleave="dropTopicId = dropTopicId === MEETING_BOARD_UNASSIGNED ? null : dropTopicId"
              @drop="onUnassignedDrop"
            >
              {{ $t('docetra.meetingBoard.unassigned') }}
              <span class="ml-1 tabular-nums text-xs">({{ unassignedMeetingCount }})</span>
            </button>
          </div>

          <div class="min-h-0 flex-1 space-y-2 overflow-y-auto p-3">
            <MeetingAppMeetingTopicSideCard
              v-for="topic in filteredTopics"
              :key="topic.id"
              :topic="topic"
              :meeting-count="topicMeetingCounts.get(topic.id) || 0"
              :selected="selectedTopicId === topic.id"
              :drop-active="dropTopicId === topic.id"
              @select="selectTopicFromPanel(topic.id)"
              @open="openTopic(topic.id)"
              @drag-over="dropTopicId = topic.id"
              @drag-leave="dropTopicId = dropTopicId === topic.id ? null : dropTopicId"
              @drop-meeting="(id) => onTopicDrop(topic.id, id)"
            />

            <p v-if="!filteredTopics.length && !pending" class="py-8 text-center text-xs text-muted">
              {{ $t('docetra.states.empty') }}
            </p>
          </div>
        </aside>

        <!-- 3 cols: meetings -->
        <section class="flex min-h-0 min-w-0 flex-1 flex-col">
          <div class="flex shrink-0 items-center gap-2 border-b border-default px-3 py-2.5">
            <UButton
              icon="i-lucide-menu"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="shrink-0 lg:hidden"
              :aria-label="$t('docetra.pages.meetingTopic')"
              :aria-expanded="topicPanelOpen"
              @click="topicPanelOpen = !topicPanelOpen"
            />
            <h2 class="min-w-0 flex-1 truncate text-sm font-semibold text-highlighted">
              {{ meetingsPanelTitle }}
            </h2>
            <div class="hidden shrink-0 items-center gap-2 lg:flex">
              <CommonAppInputDateRange
                v-model:start="meetingDateStart"
                v-model:end="meetingDateEnd"
                size="sm"
              />
            </div>
            <UPopover class="shrink-0 lg:hidden">
              <UButton
                icon="i-lucide-filter"
                :color="hasMeetingDateFilter ? 'primary' : 'neutral'"
                :variant="hasMeetingDateFilter ? 'soft' : 'ghost'"
                size="sm"
                square
                :aria-label="$t('docetra.actions.filter')"
              />
              <template #content>
                <div class="max-w-[calc(100vw-2rem)] p-3">
                  <CommonAppInputDateRange
                    v-model:start="meetingDateStart"
                    v-model:end="meetingDateEnd"
                    size="sm"
                  />
                </div>
              </template>
            </UPopover>
            <CommonAppLiveSearch
              v-model="meetingSearch"
              class="min-w-0 w-28 shrink sm:w-56"
              :placeholder="$t('docetra.meetingBoard.searchMeetings')"
            />
          </div>

          <div
            class="min-h-0 flex-1 overflow-y-auto p-3"
            @dragover.prevent
            @drop="onMeetingsPanelDrop"
          >
            <div class="grid grid-cols-1 items-stretch gap-2 sm:grid-cols-2 xl:grid-cols-3">
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
