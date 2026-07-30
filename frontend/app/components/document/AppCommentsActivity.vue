<script setup lang="ts">
import type { TimelineItem } from '@nuxt/ui'
import type { ActivityEvent, EntityComment, PersonSummary } from '~/types/docetra/common'

const props = withDefaults(defineProps<{
  comments: EntityComment[]
  activity: ActivityEvent[]
  commentBody: string
  submitting?: boolean
  canComment?: boolean
  currentUser?: PersonSummary
  showComposer?: boolean
  showNewEmail?: boolean
}>(), {
  canComment: true,
  showComposer: true,
  showNewEmail: true,
  submitting: false,
})

const emit = defineEmits<{
  'update:commentBody': [string]
  submit: []
}>()

const { t } = useI18n()
const root = ref<HTMLElement | null>(null)

const showInput = computed(() => props.canComment && props.showComposer)

type FeedKind = 'comment' | 'attachment' | 'event'

type ActivityTimelineItem = TimelineItem & {
  kind: FeedKind
  value: string
  at: number
  comment?: EntityComment
  event?: ActivityEvent
  highlight?: string | null
  slot?: 'comment' | 'line'
}

const timelineItems = computed<ActivityTimelineItem[]>(() => {
  const commentItems: ActivityTimelineItem[] = props.comments.map(comment => ({
    kind: 'comment' as const,
    value: `comment-${comment.id}`,
    at: new Date(comment.createdAt).getTime(),
    comment,
    icon: 'i-lucide-message-square',
    title: `${personLabel(comment.author.name)} ${t('docetra.comments.commented')}`,
    date: relativeTime(comment.createdAt),
    slot: 'comment' as const,
  }))

  const eventItems: ActivityTimelineItem[] = props.activity
    .filter(event => !['commented', 'comment'].includes(event.action))
    .map((event) => {
      const attachment = isAttachmentEvent(event.action)
      return {
        kind: (attachment ? 'attachment' : 'event') as FeedKind,
        value: `event-${event.id}`,
        at: new Date(event.occurredAt).getTime(),
        event,
        highlight: eventHighlight(event),
        icon: attachment ? 'i-lucide-paperclip' : 'i-lucide-circle',
        title: eventPrefix(event),
        date: relativeTime(event.occurredAt),
        slot: 'line' as const,
      }
    })

  return [...commentItems, ...eventItems].sort((a, b) => b.at - a.at)
})

function scrollTop() {
  root.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function relativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return t('docetra.meta.justNow')
  if (mins === 1) return t('docetra.meta.minuteAgo')
  if (mins < 60) return t('docetra.meta.minutesAgo', { n: mins })
  const hours = Math.floor(mins / 60)
  if (hours === 1) return t('docetra.meta.hourAgo')
  if (hours < 24) return t('docetra.meta.hoursAgo', { n: hours })
  const days = Math.floor(hours / 24)
  if (days === 1) return t('docetra.meta.dayAgo')
  return t('docetra.meta.daysAgo', { n: days })
}

function personLabel(name?: string) {
  const current = props.currentUser?.name
  if (!name) return t('docetra.activity.system')
  if (current && name === current) return t('docetra.meta.you')
  if (name === 'You' || name === t('docetra.meta.you')) return t('docetra.meta.you')
  return name
}

function isAttachmentEvent(action: string) {
  return action.toLowerCase().includes('attach')
}

function eventHighlight(event: ActivityEvent): string | null {
  const meta = event.metadata || {}
  if (typeof meta.fileName === 'string') return meta.fileName
  if (typeof meta.filename === 'string') return meta.filename
  if (typeof meta.attachment === 'string') return meta.attachment
  return null
}

function eventPrefix(event: ActivityEvent) {
  const actor = personLabel(event.actor?.name)
  const action = event.action.toLowerCase()

  if (action.includes('attach')) {
    return `${actor} ${t('docetra.activity.attached')}`
  }
  if (action.includes('creat')) {
    return `${actor} ${t('docetra.activity.createdThis')}`
  }
  if (action.includes('updat') || action.includes('edit')) {
    return `${actor} ${t('docetra.activity.lastEditedThis')}`
  }
  if (action.includes('assign')) {
    return event.summary
  }
  return event.summary
}

function onSubmit() {
  if (!props.commentBody.trim() || props.submitting) return
  emit('submit')
}

function asFeedItem(item: TimelineItem): ActivityTimelineItem {
  return item as ActivityTimelineItem
}

const commentActions = computed(() => [[
  { label: t('actions.edit'), icon: 'i-lucide-pencil' },
  { label: t('actions.delete'), icon: 'i-lucide-trash' },
]])
</script>

<template>
  <div ref="root" class="relative space-y-8 border-t border-default py-6">
    <!-- Comments -->
    <section class="space-y-3">
      <h2 class="text-base font-semibold text-highlighted">
        {{ $t('docetra.comments.title') }}
        <span class="font-normal text-muted">({{ comments.length }})</span>
      </h2>

      <div v-if="showInput" class="flex items-center gap-3">
        <UAvatar
          :alt="currentUser?.name || $t('docetra.meta.you')"
          size="sm"
        />
        <UInput
          :model-value="commentBody"
          :placeholder="$t('docetra.comments.placeholder')"
          color="neutral"
          variant="soft"
          size="md"
          class="w-full"
          :loading="submitting"
          :disabled="submitting"
          @update:model-value="(v: string | number) => emit('update:commentBody', String(v ?? ''))"
          @keydown.enter.exact.prevent="onSubmit"
        />
      </div>
    </section>

    <!-- Activity -->
    <section class="space-y-4">
      <div class="flex items-center justify-between gap-3">
        <h2 class="text-base font-semibold text-highlighted">
          {{ $t('docetra.activity.title') }}
        </h2>
        <UButton
          v-if="showNewEmail"
          size="xs"
          color="neutral"
          variant="outline"
          icon="i-lucide-plus"
          :label="$t('docetra.activity.newEmail')"
        />
      </div>

      <UTimeline
        v-if="timelineItems.length"
        :items="timelineItems"
        color="neutral"
        size="xs"
        class="w-full"
        :default-value="timelineItems[timelineItems.length - 1]?.value"
        :ui="{
          item: 'pb-1 last:pb-0',
          container: 'items-center',
          indicator: 'z-10 size-6 shrink-0 bg-default text-muted ring ring-default',
          separator: 'w-px min-h-4 flex-1 bg-gray-200 dark:bg-gray-700',
          wrapper: 'ms-1 pb-5',
          date: 'hidden',
          title: 'text-sm font-normal text-toned',
          description: 'hidden',
        }"
      >
        <!-- Comment card -->
        <template #comment-title="{ item }">
          <UCard
            variant="outline"
            :ui="{
              root: 'w-full',
              header: 'flex items-center gap-2.5 p-3 sm:px-3',
              body: 'p-3 pt-0 sm:p-3 sm:pt-0 ps-10 sm:ps-10',
            }"
          >
            <template #header>
              <UAvatar
                v-if="asFeedItem(item).comment"
                :alt="asFeedItem(item).comment!.author.name"
                size="xs"
              />
              <p class="min-w-0 flex-1 truncate text-sm text-toned">
                <span class="font-medium text-highlighted">{{ asFeedItem(item).title }}</span>
                <span class="text-muted"> • {{ asFeedItem(item).date }}</span>
              </p>
              <div class="flex shrink-0 items-center">
                <UButton
                  size="xs"
                  color="neutral"
                  variant="link"
                  class="px-1"
                  :label="$t('actions.edit')"
                />
                <UDropdownMenu :items="commentActions">
                  <UButton
                    icon="i-lucide-ellipsis"
                    color="neutral"
                    variant="ghost"
                    size="xs"
                    square
                  />
                </UDropdownMenu>
              </div>
            </template>

            <p class="whitespace-pre-wrap text-sm text-highlighted">
              {{ asFeedItem(item).comment?.body }}
            </p>
          </UCard>
        </template>

        <!-- Attachment / event text line -->
        <template #line-title="{ item }">
          <p class="text-sm leading-relaxed text-toned">
            <span class="text-highlighted">{{ asFeedItem(item).title }}</span>
            <template v-if="asFeedItem(item).highlight">
              {{ ' ' }}
              <span class="font-medium text-highlighted">{{ asFeedItem(item).highlight }}</span>
            </template>
            <span class="text-muted"> • {{ asFeedItem(item).date }}</span>
          </p>
        </template>

        <!-- Tiny bullet for plain events -->
        <template #indicator="{ item }">
          <span
            v-if="asFeedItem(item).kind === 'event'"
            class="size-2 rounded-full bg-gray-700 dark:bg-gray-300"
          />
          <UIcon
            v-else
            :name="asFeedItem(item).icon || 'i-lucide-circle'"
            class="size-3.5"
          />
        </template>
      </UTimeline>

      <p v-else class="text-sm text-muted">{{ $t('docetra.activity.empty') }}</p>
    </section>

    <div class="pointer-events-none sticky bottom-4 flex justify-end">
      <UButton
        icon="i-lucide-chevron-up"
        color="neutral"
        variant="soft"
        size="sm"
        square
        class="pointer-events-auto border border-default shadow-sm"
        @click="scrollTop"
      />
    </div>
  </div>
</template>
