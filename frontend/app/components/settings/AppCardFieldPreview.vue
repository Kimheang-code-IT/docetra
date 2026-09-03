<script setup lang="ts">
/**
 * Lightweight card preview — title chrome + body + footer with L/R align.
 */
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import type { CardFooterAlign } from '~/utils/card-fields'
import { resolveFooterAlign, splitCardSlots } from '~/utils/card-fields'

const props = defineProps<{
  entityKey: CardDisplayEntityKey
  visibleSlots: string[]
  footerAlignMap?: Partial<Record<CardDisplayEntityKey, Partial<Record<string, CardFooterAlign>>>>
}>()

const { t } = useI18n()

const isMeeting = computed(() => props.entityKey === 'meetingHistory')
const isTopic = computed(() => props.entityKey === 'meetingTopics')

const previewTitle = computed(() =>
  isTopic.value
    ? t('docetra.cardPreview.topic')
    : isMeeting.value
    ? t('docetra.cardPreview.meetingTitle')
    : t('docetra.cardPreview.recordTitle'),
)

const split = computed(() => splitCardSlots(props.entityKey, props.visibleSlots))
const showSortOrder = computed(() => split.value.titleChrome.includes('sortOrder'))
const bodySlots = computed(() => split.value.body)
const footerSlots = computed(() => {
  const slots = split.value.footer
  if (isMeeting.value && slots.includes('meetingDate') && slots.includes('recordTime')) {
    return slots.filter(s => s !== 'recordTime')
  }
  return slots
})

function alignOf(slot: string): CardFooterAlign {
  return resolveFooterAlign(props.entityKey, slot, props.footerAlignMap)
}

const footerLeft = computed(() => footerSlots.value.filter(s => alignOf(s) === 'left'))
const footerRight = computed(() => footerSlots.value.filter(s => alignOf(s) === 'right'))

function previewText(slot: string): string {
  const map: Record<string, string> = {
    topicTitle: t('docetra.cardPreview.topic'),
    status: t('docetra.status.active'),
    sortOrder: '1',
    letterNumber: 'MTG-2026-0001',
    letterDate: t('docetra.cardPreview.date'),
    meetingDate: t('docetra.cardPreview.date'),
    recordTime: t('docetra.cardPreview.date'),
    location: t('docetra.cardPreview.location'),
    attendeesCount: '12',
    participants: t('docetra.cardPreview.participants'),
    internalUnits: t('docetra.cardPreview.internalUnits'),
    externalUnits: t('docetra.cardPreview.externalUnits'),
    referenceNumber: t('docetra.cardPreview.reference'),
    recordType: t('docetra.cardPreview.recordType'),
    party: t('docetra.cardPreview.party'),
    owner: t('docetra.cardPreview.owner'),
    assignee: t('docetra.cardPreview.assignee'),
    stage: t('docetra.cardPreview.stage'),
    waiting: t('docetra.fields.waiting'),
    tags: t('docetra.cardPreview.tag'),
    description: t('docetra.cardPreview.description'),
    dateRange: t('docetra.cardPreview.date'),
    receivedDate: t('docetra.cardPreview.date'),
    sentDate: t('docetra.cardPreview.date'),
    createdAt: t('docetra.cardPreview.date'),
    updatedAt: t('docetra.cardPreview.date'),
    attachmentCount: '2',
    commentCount: '3',
    recordFlowCode: 'normal',
    recordContent: t('docetra.cardPreview.description'),
    documentType: t('docetra.cardPreview.recordType'),
    letterSubject: t('docetra.cardPreview.recordTitle'),
    documentDate: t('docetra.cardPreview.date'),
    directorGeneralDate: t('docetra.cardPreview.date'),
    directorDate: t('docetra.cardPreview.date'),
    involvedOfficers: t('docetra.cardPreview.participants'),
    officeInCharge: t('docetra.cardPreview.internalUnits'),
    officerInCharge: t('docetra.cardPreview.owner'),
  }
  return map[slot] || slot
}
</script>

<template>
  <article class="flex min-h-30 min-w-0 flex-col overflow-hidden rounded-lg border border-default bg-default p-3 text-left shadow-xs">
    <div class="flex min-w-0 items-start gap-2">
      <span
        v-if="showSortOrder"
        class="mt-0.5 shrink-0 tabular-nums text-[11px] app-card-text"
      >
        1
      </span>
      <div class="min-w-0 flex-1 overflow-hidden">
        <div class="flex min-w-0 flex-wrap items-center gap-1.5">
          <p class="min-w-0 max-w-full line-clamp-2 text-sm font-semibold text-highlighted wrap-break-word">
            {{ previewTitle }}
          </p>
        </div>
        <p
          v-if="bodySlots.includes('topicTitle')"
          class="mt-1 truncate text-xs app-card-text"
        >
          {{ previewText('topicTitle') }}
        </p>
      </div>
      <UButton
        icon="i-lucide-ellipsis"
        color="neutral"
        variant="ghost"
        size="xs"
        class="pointer-events-none shrink-0 opacity-60"
        tabindex="-1"
      />
    </div>

    <div class="min-h-0 flex-1">
      <template v-for="slot in bodySlots" :key="slot">
      <p
        v-if="slot === 'referenceNumber' || slot === 'recordType' || slot === 'description' || slot === 'letterNumber'"
        class="mt-1.5 truncate text-xs app-card-text"
      >
        {{ previewText(slot) }}
      </p>
      <div
        v-else-if="slot === 'waiting' || slot === 'tags'"
        class="app-card-field-highlight mt-1.5 text-xs"
        :class="slot === 'waiting' ? 'app-card-field-highlight--warning' : 'app-card-field-highlight--secondary'"
      >
        <UIcon
          :name="slot === 'waiting' ? 'i-lucide-clock-3' : 'i-lucide-tag'"
          class="size-3 shrink-0"
        />
        <span class="truncate">{{ previewText(slot) }}</span>
      </div>
      <div
        v-else-if="slot === 'party' || slot === 'owner' || slot === 'assignee' || slot === 'participants' || slot === 'internalUnits' || slot === 'externalUnits'"
        class="mt-1.5 flex items-center gap-1.5 truncate text-xs app-card-text"
      >
        <UIcon
          :name="slot === 'party' || slot === 'internalUnits' ? 'i-lucide-building-2'
            : slot === 'externalUnits' ? 'i-lucide-landmark'
              : slot === 'participants' ? 'i-lucide-users'
            : slot === 'assignee' ? 'i-lucide-user-check'
              : 'i-lucide-user'"
          class="size-3 shrink-0"
        />
        <span class="truncate">{{ previewText(slot) }}</span>
      </div>
      <div
        v-else
        class="mt-1.5 flex min-w-0 items-center gap-1.5 truncate text-xs app-card-text"
      >
        <span class="shrink-0 font-medium text-toned">{{ $t(`docetra.cardSlots.${slot}`) }}:</span>
        <span class="truncate">{{ previewText(slot) }}</span>
      </div>
    </template>
    </div>

    <div
      v-if="footerSlots.length"
      class="mt-auto flex items-center justify-between gap-2 border-t border-default pt-2 text-xs app-card-text"
    >
      <div class="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
        <span
          v-for="slot in footerLeft"
          :key="`L-${slot}`"
          class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
          :class="slot === 'location' ? 'app-card-field-highlight--warning' : 'app-card-field-highlight--info'"
        >
          <UIcon
            :name="slot === 'location' ? 'i-lucide-map-pin'
              : slot === 'attendeesCount' ? 'i-lucide-users'
                : slot === 'attachmentCount' ? 'i-lucide-paperclip'
                  : slot === 'commentCount' ? 'i-lucide-message-circle'
                    : 'i-lucide-calendar'"
            class="size-3 shrink-0"
          />
          <span class="truncate">{{ previewText(slot) }}</span>
        </span>
      </div>
      <div class="inline-flex shrink-0 flex-wrap items-center justify-end gap-2">
        <span
          v-for="slot in footerRight"
          :key="`R-${slot}`"
          class="app-card-field-highlight--compact inline-flex items-center gap-1"
          :class="slot === 'location' ? 'app-card-field-highlight--warning' : slot === 'attachmentCount' ? 'app-card-field-highlight--secondary' : 'app-card-field-highlight--info'"
        >
          <UIcon
            :name="slot === 'location' ? 'i-lucide-map-pin'
              : slot === 'attendeesCount' ? 'i-lucide-users'
                : slot === 'attachmentCount' ? 'i-lucide-paperclip'
                  : slot === 'commentCount' ? 'i-lucide-message-circle'
                    : 'i-lucide-calendar'"
            class="size-3"
          />
          {{ previewText(slot) }}
        </span>
      </div>
    </div>
  </article>
</template>
