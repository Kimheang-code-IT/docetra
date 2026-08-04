<script setup lang="ts">
import { useMeetingTopicBoard } from '~/composables/meeting/useMeetingTopicBoard'

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
  filteredTopics,
  filteredMeetings,
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

const notesOpen = ref(false)
const notesMeetingId = ref<string | null>(null)

/** Add Topic always; Add Meeting only on standalone (All meetings) view. */
const createButtons = computed(() => {
  const buttons = [
    { labelKey: 'docetra.meetingBoard.createTopic', icon: 'i-lucide-messages-square' },
  ]
  if (selectedTopicId.value == null) {
    buttons.push({ labelKey: 'docetra.meetingBoard.createMeeting', icon: 'i-lucide-calendar-plus' })
  }
  return buttons
})

function onCreateButton(index: number) {
  if (index === 0) openCreateTopic()
  else openCreateMeeting()
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

async function onReorderBefore(beforeId: string | null) {
  if (!draggingMeetingId.value || !selectedTopicId.value) return
  await reorderMeeting(draggingMeetingId.value, beforeId)
  draggingMeetingId.value = null
}

function onMeetingsPanelDrop(event: DragEvent) {
  event.preventDefault()
  if (!selectedTopicId.value || !draggingMeetingId.value) return
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

      <div class="grid min-h-0 flex-1 grid-cols-1 gap-0 lg:grid-cols-4">
        <!-- 1 col: topics -->
        <aside class="flex min-h-0 flex-col border-b border-default lg:border-b-0 lg:border-r">
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
              :class="selectedTopicId == null
                ? 'border-primary bg-primary/5 font-medium text-highlighted ring-1 ring-primary/25'
                : 'border-default text-muted hover:border-primary/30'"
              @click="selectTopic(null)"
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
              @select="selectTopic(topic.id)"
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
        <section class="flex min-h-0 flex-col lg:col-span-3">
          <div class="flex shrink-0 flex-col gap-2 border-b border-default px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between">
            <h2 class="min-w-0 truncate text-sm font-semibold text-highlighted">
              {{ selectedTopic?.title || $t('docetra.meetingBoard.allMeetings') }}
            </h2>
            <div class="flex w-full flex-wrap items-center gap-2 sm:w-auto sm:justify-end">
              <CommonAppInputDateRange
                v-model:start="meetingDateStart"
                v-model:end="meetingDateEnd"
                size="sm"
              />
              <CommonAppLiveSearch
                v-model="meetingSearch"
                class="w-full sm:w-56"
                :placeholder="$t('docetra.meetingBoard.searchMeetings')"
              />
            </div>
          </div>

          <div
            class="min-h-0 flex-1 overflow-y-auto p-3"
            @dragover.prevent
            @drop="onMeetingsPanelDrop"
          >
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
              <MeetingAppMeetingBoardCard
                v-for="meeting in filteredMeetings"
                :key="meeting.id"
                :meeting="meeting"
                :topics="topics"
                :dragging="draggingMeetingId === meeting.id"
                :show-topic="!selectedTopicId"
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
