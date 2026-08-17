<script setup lang="ts">
import type { MeetingHistory } from '~/types/docetra/entities'
import {
  TABLE_PAGE_SIZES,
  paginationItemsPerPage,
  parsePageLimit,
} from '~/utils/pagination'

const props = defineProps<{
  rows: Record<string, unknown>[]
  total: number
  page: number
  limit: number
  pending?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  'update:page': [number]
  'update:limit': [number]
  open: [row: Record<string, unknown>]
  retry: []
}>()

const { t, te, locale } = useI18n()

const meetings = computed(() => props.rows as unknown as MeetingHistory[])
const pageSizeItems = computed(() => [
  ...TABLE_PAGE_SIZES.map(size => ({ label: String(size), value: String(size) })),
])
const pageSizeModel = computed({
  get: () => String(props.limit),
  set: value => emit('update:limit', parsePageLimit(value, 10)),
})
const effectiveItemsPerPage = computed(() => paginationItemsPerPage(props.limit, props.total))
const visibleRange = computed(() => {
  if (!props.total || !props.rows.length) return { start: 0, end: 0 }
  const start = ((props.page - 1) * props.limit) + 1
  return { start, end: Math.min(start + props.rows.length - 1, props.total) }
})

function dateParts(value?: string) {
  const date = value ? new Date(value) : null
  if (!date || Number.isNaN(date.getTime())) return { day: '—', month: '', full: '—' }
  const code = locale.value === 'km' ? 'km-KH' : 'en-US'
  return {
    day: new Intl.DateTimeFormat(code, { day: '2-digit' }).format(date),
    month: new Intl.DateTimeFormat(code, { month: 'short', year: 'numeric' }).format(date),
    full: new Intl.DateTimeFormat(code, { dateStyle: 'medium', timeStyle: 'short' }).format(date),
  }
}

function translated(group: string, value?: string) {
  if (!value) return ''
  const key = `docetra.${group}.${value}`
  return te(key) ? t(key) : value.replaceAll('_', ' ')
}

function badgeColor(value?: string): 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info' {
  const normalized = String(value || '').toLowerCase()
  if (normalized === 'completed' || normalized === 'active') return 'success'
  if (normalized === 'draft' || normalized === 'pending' || normalized === 'review') return 'warning'
  if (normalized === 'failed' || normalized === 'disabled') return 'error'
  if (normalized === 'approval') return 'primary'
  return 'info'
}

function listText(value: unknown) {
  if (Array.isArray(value)) return value.map(String).filter(Boolean).join(', ')
  return String(value || '')
}

function participantCount(meeting: MeetingHistory) {
  if (meeting.attendeesCount != null) return meeting.attendeesCount
  return Array.isArray(meeting.participants) ? meeting.participants.length : 0
}

function openMeeting(meeting: MeetingHistory) {
  emit('open', meeting as unknown as Record<string, unknown>)
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div v-if="error" class="flex min-h-48 flex-1 flex-col items-center justify-center gap-3 p-6 text-center">
      <UIcon name="i-lucide-circle-alert" class="size-8 text-error" />
      <p class="text-sm text-muted">{{ error }}</p>
      <UButton icon="i-lucide-refresh-cw" color="neutral" variant="outline" @click="emit('retry')">
        {{ $t('docetra.actions.retry') }}
      </UButton>
    </div>

    <div v-else class="min-h-0 flex-1 overflow-y-auto px-3 py-4 sm:px-5">
      <div v-if="pending" class="flex justify-center py-16">
        <UIcon name="i-lucide-loader-circle" class="size-7 animate-spin text-primary" />
      </div>

      <div v-else-if="!meetings.length" class="flex flex-col items-center justify-center gap-2 py-16 text-muted">
        <UIcon name="i-lucide-calendar-x-2" class="size-9" />
        <p class="text-sm">{{ $t('docetra.states.empty') }}</p>
      </div>

      <ol v-else class="relative mx-auto max-w-5xl space-y-4 before:absolute before:bottom-5 before:left-[2.35rem] before:top-5 before:w-px before:bg-accented sm:before:left-[8.45rem]">
        <li
          v-for="meeting in meetings"
          :key="meeting.id"
          class="relative grid grid-cols-[4.75rem_minmax(0,1fr)] gap-3 sm:grid-cols-[8rem_minmax(0,1fr)] sm:gap-5"
        >
          <div class="relative z-10 flex items-start justify-between gap-2 sm:block sm:text-right">
            <div class="rounded-md bg-default px-1 py-1 sm:px-2">
              <div class="text-xl font-bold leading-none text-highlighted">{{ dateParts(meeting.meetingDate).day }}</div>
              <div class="mt-1 text-[0.68rem] font-medium uppercase tracking-wide text-muted">{{ dateParts(meeting.meetingDate).month }}</div>
            </div>
            <span class="absolute -right-[1.04rem] top-4 size-3 rounded-full border-2 border-primary bg-default shadow-sm sm:-right-[1.78rem]" />
          </div>

          <button
            type="button"
            class="group min-w-0 rounded-lg border border-default bg-default p-3 text-left shadow-xs transition hover:-translate-y-px hover:border-primary/50 hover:shadow-sm sm:p-4"
            @click="openMeeting(meeting)"
          >
            <div class="flex min-w-0 items-start gap-3">
              <span class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <UIcon name="i-lucide-calendar-clock" class="size-5" />
              </span>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-1.5">
                  <h3 class="min-w-0 flex-1 truncate font-semibold text-highlighted group-hover:text-primary">{{ meeting.title }}</h3>
                  <UBadge :color="badgeColor(meeting.status)" variant="soft" size="sm">
                    {{ translated('status', meeting.status) }}
                  </UBadge>
                  <UBadge v-if="meeting.stage" :color="badgeColor(meeting.stage)" variant="subtle" size="sm">
                    {{ translated('stages', meeting.stage) }}
                  </UBadge>
                </div>
                <div class="mt-2 flex flex-wrap gap-2 text-xs text-toned">
                  <span class="app-card-field-highlight app-card-field-highlight--info inline-flex items-center gap-1">
                    <UIcon name="i-lucide-clock-3" class="size-3.5" />
                    {{ dateParts(meeting.meetingDate).full }}
                  </span>
                  <span v-if="meeting.letterNumber" class="app-card-field-highlight app-card-field-highlight--secondary inline-flex items-center gap-1">
                    <UIcon name="i-lucide-hash" class="size-3.5" />
                    {{ meeting.letterNumber }}
                  </span>
                  <span v-if="meeting.location" class="app-card-field-highlight app-card-field-highlight--warning inline-flex items-center gap-1">
                    <UIcon name="i-lucide-map-pin" class="size-3.5" />
                    {{ meeting.location }}
                  </span>
                  <span v-if="meeting.meetingMode" class="app-card-field-highlight app-card-field-highlight--secondary inline-flex items-center gap-1">
                    <UIcon name="i-lucide-video" class="size-3.5" />
                    {{ translated('meetingMode', meeting.meetingMode) }}
                  </span>
                  <span v-if="participantCount(meeting)" class="app-card-field-highlight app-card-field-highlight--success inline-flex items-center gap-1">
                    <UIcon name="i-lucide-users" class="size-3.5" />
                    {{ participantCount(meeting) }}
                  </span>
                </div>
                <p v-if="listText(meeting.participants)" class="mt-2 line-clamp-1 text-xs app-card-text">
                  {{ listText(meeting.participants) }}
                </p>
              </div>
              <UIcon name="i-lucide-chevron-right" class="mt-1 size-4 shrink-0 text-muted transition group-hover:translate-x-0.5 group-hover:text-primary" />
            </div>
          </button>
        </li>
      </ol>
    </div>

    <div v-if="!error" class="flex shrink-0 items-center justify-between gap-2 border-t border-default bg-default px-2 py-2 sm:px-3">
      <div class="flex shrink-0 items-center gap-2 text-sm text-toned">
        <span class="hidden sm:inline">{{ $t('common.rowsPerPage') }}</span>
        <USelect
          v-model="pageSizeModel"
          :items="pageSizeItems"
          value-key="value"
          size="sm"
          class="w-17 sm:w-22"
          :content="{ side: 'top', align: 'start', sideOffset: 6 }"
          :aria-label="$t('common.rowsPerPage')"
        />
        <span class="hidden whitespace-nowrap text-xs text-muted md:inline">
          {{ $t('common.showingRows', { start: visibleRange.start, end: visibleRange.end, total }) }}
        </span>
      </div>
      <UPagination
        :page="page"
        :total="total"
        :items-per-page="effectiveItemsPerPage"
        :sibling-count="0"
        show-edges
        size="sm"
        color="neutral"
        variant="outline"
        active-color="primary"
        active-variant="solid"
        @update:page="(value: number) => emit('update:page', value)"
      />
    </div>
  </div>
</template>
