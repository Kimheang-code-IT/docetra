<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import {
  MEETING_BOARD_UNASSIGNED,
  useMeetingTopicBoard,
} from '~/composables/meeting/useMeetingTopicBoard'
import { useBoardDragDrop } from '~/composables/common/useBoardDragDrop'
import { useBoardViewMode } from '~/composables/common/useBoardViewMode'
import { consumeListStale } from '~/utils/workspace-list-stale'
import { permissionForAction } from '~/utils/role/access'
import { useConfirm } from '~/composables/common/useConfirm'
import { getEntityConfig } from '~/config/entities'
import { getByPath } from '~/utils/object-path'
import { useCardFields } from '~/composables/settings/useCardFields'
import { splitCardSlots } from '~/utils/card-fields'
import type { RowActionItem } from '~/types/docetra/row-actions'
import type { MeetingTopic } from '~/types/docetra/entities'

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
  refresh,
  loadMoreTopics,
  loadMoreMeetings,
  selectTopic,
  assignMeetingToTopic,
  reorderMeeting,
  deleteTopic,
  deleteMeeting,
  createTopic,
  updateTopicTitle,
  setTopicActive,
  openMeeting,
  openCreateMeeting,
} = useMeetingTopicBoard()

const { t, te } = useI18n()
const toast = useToast()
const { confirm } = useConfirm()
const auth = useAuthStore()
const viewMode = useBoardViewMode('meeting-topic-view-mode', 'cards')
const {
  draggingId,
  dropTargetId,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDragLeave,
  consumeDrop,
} = useBoardDragDrop()

const notesOpen = ref(false)
const notesMeetingId = ref<string | null>(null)
const topicPanelOpen = ref(false)
const topicListCollapsed = useState('meeting-topic-left-collapsed', () => false)
const isSmallScreen = useMediaQuery('(max-width: 1023px)')
const topicPanelCollapsed = computed(() =>
  isSmallScreen.value ? false : topicListCollapsed.value,
)

const topicDialogOpen = ref(false)
const topicDialogLoading = ref(false)
const editingTopic = ref<MeetingTopic | null>(null)

const { visibleSlots } = useCardFields('meetingTopics')
const meetingHistoryConfig = getEntityConfig('meetingHistory')
const tableColumns = computed(() => meetingHistoryConfig.columns || [])

const canCreateTopic = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_topic.view', 'create')),
)
const canEditTopic = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_topic.view', 'edit')),
)
const canArchiveTopic = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_topic.view', 'archive')),
)
const canRestoreTopic = computed(() =>
  auth.canAccessPage(permissionForAction('records.meeting_topic.view', 'restore')),
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

const tableRowActions = computed<RowActionItem[]>(() => [
  { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
  ...(canEditMeeting.value
    ? [{ key: 'notes', labelKey: 'docetra.meetingBoard.openNotes', icon: 'i-lucide-sticky-note' } satisfies RowActionItem]
    : []),
  ...(canDeleteMeeting.value
    ? [{ key: 'delete', labelKey: 'docetra.rowActions.delete', icon: 'i-lucide-trash-2', color: 'error' } satisfies RowActionItem]
    : []),
])

function topicMenuItems(topic: MeetingTopic) {
  const items: Array<Array<Record<string, unknown>>> = []
  const isActive = String(topic.status || 'active') === 'active'

  if (canEditTopic.value) {
    items.push([{
      label: t('docetra.meetingBoard.editTopic'),
      icon: 'i-lucide-pencil',
      onSelect: () => openEditTopicDialog(topic.id),
    }])
  }

  const canToggle = isActive ? canArchiveTopic.value : canRestoreTopic.value
  if (canToggle) {
    items.push([{
      label: isActive
        ? t('docetra.rowActions.deactivate')
        : t('docetra.rowActions.activate'),
      icon: isActive ? 'i-lucide-power-off' : 'i-lucide-power',
      color: isActive ? 'warning' : 'success',
      onSelect: () => onToggleTopicActive(topic.id, !isActive),
    }])
  }

  if (canDeleteTopic.value) {
    items.push([{
      label: t('docetra.rowActions.delete'),
      icon: 'i-lucide-trash-2',
      color: 'error',
      onSelect: () => onDeleteTopic(topic.id),
    }])
  }

  return items
}

function topicCardSlots(topic: MeetingTopic) {
  const slots = splitCardSlots('meetingTopics', visibleSlots.value)
  const tags = Array.isArray(topic.tags) ? topic.tags.map(String).filter(Boolean) : []
  return {
    showTags: slots.body.includes('tags') && tags.length > 0,
    tag: tags[0] || '',
    showRecordTime: slots.footer.includes('recordTime'),
    recordTime: topic.recordTime || topic.meetingDate || '—',
  }
}

function cellValue(row: Record<string, unknown>, key: string) {
  const value = getByPath(row, key)
  if (value == null || value === '') return '—'
  if (Array.isArray(value)) return value.map(String).filter(Boolean).join(', ') || '—'
  const text = String(value)
  if (key === 'status' || key === 'stage') {
    const statusKey = `docetra.status.${text}`
    const stageKey = `docetra.stages.${text}`
    if (te(statusKey)) return t(statusKey)
    if (te(stageKey)) return t(stageKey)
  }
  return text
}

function openCreateTopicDialog() {
  editingTopic.value = null
  topicDialogOpen.value = true
}

function openEditTopicDialog(topicId: string) {
  if (!canEditTopic.value) return
  const topic = topics.value.find(item => item.id === topicId) || null
  if (!topic) return
  editingTopic.value = topic
  topicDialogOpen.value = true
}

function onCreateButton(index: number) {
  const button = createButtons.value[index]
  if (!button) return
  if (button.labelKey === 'docetra.meetingBoard.createTopic') openCreateTopicDialog()
  else openCreateMeeting()
}

function selectTopicFromPanel(topicId: string | null) {
  selectTopic(topicId)
  if (isSmallScreen.value) topicPanelOpen.value = false
}

onMounted(() => {
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
  onDragStart(id)
}

function onTopicDrop(topicId: string) {
  if (!canAssignMeeting.value) return
  const meetingId = consumeDrop()
  if (!meetingId) return
  assignMeetingToTopic(meetingId, topicId)
}

function onUnassignedDrop() {
  if (!canAssignMeeting.value) return
  const meetingId = consumeDrop()
  if (!meetingId) return
  assignMeetingToTopic(meetingId, null)
}

async function onReorderBefore(beforeId: string | null) {
  if (!canAssignMeeting.value || !draggingId.value || isPoolView.value) return
  await reorderMeeting(draggingId.value, beforeId)
  onDragEnd()
}

function onMeetingsPanelDrop() {
  if (isPoolView.value || !draggingId.value) return
  void onReorderBefore(null)
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

async function onToggleTopicActive(id: string, active: boolean) {
  if (active ? !canRestoreTopic.value : !canArchiveTopic.value) return
  try {
    await setTopicActive(id, active)
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
  }
}

async function onSaveTopicName(payload: { title: string, description: string }) {
  if (topicDialogLoading.value) return
  topicDialogLoading.value = true
  try {
    if (editingTopic.value?.id) {
      await updateTopicTitle(editingTopic.value.id, payload.title, payload.description)
    }
    else {
      if (!canCreateTopic.value) return
      await createTopic(payload.title, payload.description)
    }
    topicDialogOpen.value = false
    editingTopic.value = null
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.meetingBoard.topicSaveFailed'), color: 'error' })
  }
  finally {
    topicDialogLoading.value = false
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

function onRowAction(payload: { key: string, row: Record<string, unknown> }) {
  const id = String(payload.row.id || '')
  if (!id) return
  if (payload.key === 'detail') {
    openMeeting(id)
    return
  }
  if (payload.key === 'notes') {
    openMeetingNotes(id)
    return
  }
  if (payload.key === 'delete') void onDeleteMeeting(id)
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
      v-model:view-mode="viewMode"
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
        <div
          class="flex"
          :class="topicPanelCollapsed ? 'flex-col items-center gap-1.5' : 'flex-row items-stretch gap-2'"
        >
          <WorkspaceAppBoardRailPill
            class="min-w-0 flex-1"
            :label="$t('docetra.meetingBoard.allMeetings')"
            :count="allMeetingCount"
            icon="i-lucide-layout-grid"
            :selected="isAllMeetings"
            :collapsed="topicPanelCollapsed"
            :stacked="false"
            @select="selectTopicFromPanel(null)"
          />
          <WorkspaceAppBoardRailPill
            class="min-w-0 flex-1"
            :label="$t('docetra.meetingBoard.unassigned')"
            :count="unassignedMeetingCount"
            icon="i-lucide-circle-dashed"
            :selected="isUnassigned"
            :collapsed="topicPanelCollapsed"
            :stacked="false"
            :droppable="canAssignMeeting"
            :drop-active="dropTargetId === MEETING_BOARD_UNASSIGNED"
            drop-data-attr="meeting-topic-drop"
            :drop-value="MEETING_BOARD_UNASSIGNED"
            @select="selectTopicFromPanel(MEETING_BOARD_UNASSIGNED)"
            @drag-over="onDragOver(MEETING_BOARD_UNASSIGNED)"
            @drag-leave="onDragLeave(MEETING_BOARD_UNASSIGNED)"
            @drop="onUnassignedDrop"
          />
        </div>
      </template>

      <template #rail-items>
        <WorkspaceAppBoardRailItem
          v-for="topic in filteredTopics"
          :key="topic.id"
          :title="topic.title"
          :count="topicMeetingCounts.get(topic.id) || 0"
          icon="i-lucide-message-square"
          :selected="selectedTopicId === topic.id"
          :collapsed="topicPanelCollapsed"
          :drop-active="dropTargetId === topic.id"
          :can-drop="canAssignMeeting && String(topic.status || 'active') === 'active'"
          :disabled="String(topic.status || 'active') !== 'active'"
          drop-data-attr="meeting-topic-drop"
          :drop-value="topic.id"
          @select="selectTopicFromPanel(topic.id)"
          @open="canEditTopic && openEditTopicDialog(topic.id)"
          @drag-over="onDragOver(topic.id)"
          @drag-leave="onDragLeave(topic.id)"
          @drop="onTopicDrop(topic.id)"
        >
          <template v-if="topic.description" #subtitle>
            <p class="mt-1 line-clamp-2 text-xs app-card-text">
              {{ topic.description }}
            </p>
          </template>
          <template v-if="topicMenuItems(topic).length" #actions>
            <UDropdownMenu :items="topicMenuItems(topic)" :content="{ align: 'end' }">
              <UButton
                icon="i-lucide-ellipsis"
                color="neutral"
                variant="ghost"
                size="xs"
                class="shrink-0"
                :aria-label="$t('docetra.actions.more')"
                @click.stop
              />
            </UDropdownMenu>
          </template>
          <template #body>
            <div
              v-if="topicCardSlots(topic).showTags"
              class="mt-2 flex flex-wrap gap-x-2 gap-y-1"
            >
              <span class="app-card-field-highlight app-card-field-highlight--secondary text-xs">
                <UIcon name="i-lucide-tag" class="size-3 shrink-0" />
                <span class="truncate">{{ topicCardSlots(topic).tag }}</span>
              </span>
            </div>
            <div
              v-if="topicCardSlots(topic).showRecordTime"
              class="app-card-field-highlight app-card-field-highlight--info mt-2 flex items-center gap-1 text-xs app-card-text"
            >
              <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
              <span class="truncate">{{ topicCardSlots(topic).recordTime }}</span>
            </div>
          </template>
        </WorkspaceAppBoardRailItem>

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

      <WorkspaceAppBoardContent
        :view-mode="viewMode"
        :pending="pending"
        :empty="!filteredMeetings.length"
        empty-icon="i-lucide-calendar-off"
        empty-label-key="docetra.meetingBoard.emptyMeetings"
        :has-more="hasMoreMeetings"
        :loading-more="loadingMoreMeetings"
        :columns="tableColumns"
        :rows="filteredMeetings as unknown as Record<string, unknown>[]"
        :total="filteredMeetings.length"
        :page="1"
        :limit="Math.max(filteredMeetings.length, 1)"
        :cell-value="cellValue"
        :row-actions="tableRowActions"
        :selectable="false"
        :can-delete="canDeleteMeeting"
        :show-meta="true"
        :table-error="error"
        :panel-droppable="!isPoolView && canAssignMeeting"
        @load-more="loadMoreMeetings"
        @row-click="(row) => openMeeting(String(row.id || ''))"
        @row-action="onRowAction"
        @retry="refresh"
        @panel-drop="onMeetingsPanelDrop"
      >
        <RecordAppRecordBoardCard
          v-for="meeting in filteredMeetings"
          :key="meeting.id"
          :meeting="meeting"
          :topics="topics"
          :title="meeting.title"
          entity-key="meetingHistory"
          :dragging="draggingId === meeting.id"
          :show-topic="isPoolView"
          :can-assign="canAssignMeeting"
          :can-edit-notes="canEditMeeting"
          :can-delete="canDeleteMeeting"
          @open="openMeeting(meeting.id)"
          @open-notes="openMeetingNotes(meeting.id)"
          @drag-start="onMeetingDragStart"
          @drag-end="onDragEnd"
          @assign="(topicId) => canAssignMeeting && assignMeetingToTopic(meeting.id, topicId)"
          @reorder-before="onReorderBefore"
          @delete="onDeleteMeeting(meeting.id)"
        />
      </WorkspaceAppBoardContent>
    </WorkspaceAppBoardShell>

    <MeetingAppMeetingNotesDialog
      v-if="notesOpen && notesMeetingId"
      v-model:open="notesOpen"
      :meeting-id="notesMeetingId"
      @saved="onNotesSaved"
      @closed="onNotesClosed"
    />

    <MeetingAppMeetingTopicNameDialog
      v-model:open="topicDialogOpen"
      :topic="editingTopic"
      :loading="topicDialogLoading"
      @save="onSaveTopicName"
    />
  </WorkspaceAppWorkspacePage>
</template>
