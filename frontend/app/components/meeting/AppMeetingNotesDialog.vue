<script setup lang="ts">
import type { MeetingHistory } from '~/types/docetra/entities'
import type { AttachmentMeta } from '~/types/docetra/common'
import { getEntityAdapter } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'

const open = defineModel<boolean>('open', { default: false })

const props = defineProps<{
  meetingId: string | null
}>()

const emit = defineEmits<{
  saved: [meeting: MeetingHistory]
}>()

const { t } = useI18n()
const toast = useToast()
const { confirm } = useConfirm()
const meetingsAdapter = getEntityAdapter('meetingHistory')

const pending = ref(false)
const saving = ref(false)
const meeting = ref<MeetingHistory | null>(null)
const notes = ref('')
const attachments = ref<AttachmentMeta[]>([])
const dirty = ref(false)

async function load() {
  if (!props.meetingId) return
  pending.value = true
  dirty.value = false
  try {
    const [meetingRes, filesRes] = await Promise.all([
      meetingsAdapter.get(props.meetingId),
      meetingsAdapter.listAttachments?.(props.meetingId),
    ])
    meeting.value = meetingRes.data as MeetingHistory
    notes.value = meeting.value.notes || ''
    attachments.value = (filesRes?.data || []) as AttachmentMeta[]
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.meetingNotes.loadFailed'), color: 'error' })
    open.value = false
  }
  finally {
    pending.value = false
  }
}

watch(
  () => [open.value, props.meetingId] as const,
  ([isOpen, id]) => {
    if (isOpen && id) load()
    if (!isOpen) {
      meeting.value = null
      notes.value = ''
      attachments.value = []
      dirty.value = false
    }
  },
  { immediate: true },
)

watch(notes, () => {
  if (!pending.value && meeting.value) dirty.value = true
})

function onUploadsComplete(files: AttachmentMeta[]) {
  attachments.value = [...files, ...attachments.value]
  if (meeting.value) {
    meeting.value.attachmentCount = attachments.value.length
  }
  dirty.value = true
  toast.add({ title: t('docetra.attachments.uploaded'), color: 'success' })
}

function removeAttachment(id: string) {
  attachments.value = attachments.value.filter(f => f.id !== id)
  if (meeting.value) meeting.value.attachmentCount = attachments.value.length
  dirty.value = true
}

async function save() {
  if (!props.meetingId || !meeting.value) return
  const ok = await confirm({ kind: 'save' })
  if (!ok) return
  saving.value = true
  try {
    const res = await meetingsAdapter.update(props.meetingId, {
      notes: notes.value,
      attachmentCount: attachments.value.length,
    } as any)
    if (meetingsAdapter.replaceAttachments) {
      await meetingsAdapter.replaceAttachments(props.meetingId, attachments.value)
    }
    meeting.value = res.data as MeetingHistory
    dirty.value = false
    emit('saved', meeting.value)
    const { indexMeetingNotesForSearch, indexFileForSearch } = await import('~/utils/search/index-hooks')
    indexMeetingNotesForSearch({
      meetingId: props.meetingId,
      title: meeting.value.title,
      notes: notes.value,
    })
    for (const file of attachments.value) {
      indexFileForSearch({
        entityId: props.meetingId,
        indexId: `idx:att:meeting:${props.meetingId}:${file.id}`,
        fileName: file.name,
        mimeType: file.mimeType,
        url: `/meetings/history/${props.meetingId}`,
        permission: 'meetings.history.view',
        contextTitle: meeting.value.title,
        entityType: 'attachment',
      })
    }
    toast.add({ title: t('docetra.meetingNotes.saved'), color: 'success' })
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.meetingNotes.saveFailed'), color: 'error' })
  }
  finally {
    saving.value = false
  }
}

async function onClose(value: boolean) {
  if (!value && dirty.value) {
    const ok = await confirm({ kind: 'unsaved' })
    if (!ok) {
      open.value = true
      return
    }
  }
  open.value = value
}
</script>

<template>
  <UModal
    :open="open"
    fullscreen
    :ui="{
      content: 'bg-default flex flex-col h-dvh max-h-dvh overflow-hidden',
      header: 'shrink-0 border-b border-default px-4 py-3',
      body: 'flex-1 min-h-0 overflow-hidden p-0',
      footer: 'shrink-0 border-t border-default px-4 py-3',
    }"
    @update:open="onClose"
  >
    <template #header>
      <div class="flex w-full min-w-0 items-center gap-3">
        <h2 class="min-w-0 flex-1 truncate text-base font-semibold text-highlighted">
          {{ meeting?.title || $t('docetra.meetingNotes.title') }}
        </h2>
        <div class="flex shrink-0 items-center gap-2">
          <span
            v-if="meeting?.meetingDate"
            class="inline-flex items-center gap-1.5 text-sm text-muted"
          >
            <UIcon name="i-lucide-calendar" class="size-3.5" />
            {{ meeting.meetingDate }}
          </span>
          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            size="sm"
            :aria-label="$t('actions.close')"
            @click="onClose(false)"
          />
        </div>
      </div>
    </template>

    <template #body>
      <div v-if="pending" class="flex h-full items-center justify-center">
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <div
        v-else
        class="grid h-full min-h-0 grid-cols-1 divide-y divide-default lg:grid-cols-4 lg:divide-x lg:divide-y-0"
      >
        <!-- Editor: 3 cols -->
        <section class="flex h-full min-h-0 flex-col p-4 lg:col-span-3">
          <LazyCommonAppRichTextNote
            :key="`note-${meetingId}`"
            v-model="notes"
            fill
            class="min-h-64 h-full flex-1"
          />
        </section>

        <!-- Files: 1 col -->
        <section class="flex h-full min-h-0 flex-col gap-3 overflow-y-auto p-4 lg:col-span-1">
          <LazyCommonAppUppyUploader
            v-if="meetingId && !pending"
            :key="`uppy-${meetingId}`"
            :entity-id="meetingId"
            :endpoint="`/api/v2/meetings/history/${encodeURIComponent(meetingId)}/attachments`"
            :height="260"
            @complete="onUploadsComplete"
          />

          <ul class="space-y-2">
            <li
              v-for="file in attachments"
              :key="file.id"
              class="flex items-center justify-between gap-2 rounded-lg border border-default px-3 py-2 text-sm"
            >
              <div class="flex min-w-0 items-center gap-2">
                <UIcon name="i-lucide-paperclip" class="size-4 shrink-0 text-muted" />
                <span class="truncate">{{ file.name }}</span>
              </div>
              <div class="flex shrink-0 items-center gap-1">
                <span class="text-xs text-muted">{{ Math.round(file.sizeBytes / 1024) }} KB</span>
                <UButton
                  icon="i-lucide-trash-2"
                  color="neutral"
                  variant="ghost"
                  size="xs"
                  :aria-label="$t('actions.delete')"
                  @click="removeAttachment(file.id)"
                />
              </div>
            </li>
            <li v-if="!attachments.length" class="text-sm text-muted">
              {{ $t('docetra.states.noAttachments') }}
            </li>
          </ul>
        </section>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full items-center justify-end gap-2">
        <UButton
          color="neutral"
          variant="ghost"
          :label="$t('actions.cancel')"
          @click="onClose(false)"
        />
        <UButton
          color="primary"
          :label="$t('actions.save')"
          :loading="saving"
          :disabled="pending || !dirty"
          @click="save"
        />
      </div>
    </template>
  </UModal>
</template>
