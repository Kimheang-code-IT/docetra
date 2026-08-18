<script setup lang="ts">
import type { DashboardCalendarEvent } from '~/types/docetra/entities'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

const props = withDefaults(
  defineProps<{
    events?: DashboardCalendarEvent[]
    /** Max event chips shown per day cell before “+N more” */
    maxVisible?: number
  }>(),
  {
    events: () => [],
    maxVisible: 3,
  },
)

const emit = defineEmits<{
  eventClick: [DashboardCalendarEvent]
  daySelect: [dateKey: string]
}>()

const { t } = useI18n()
const { localization, formatDatePart } = useAppLocalization()

const viewCursor = ref(startOfMonth(new Date()))
const selectedKey = ref(toDateKey(new Date()))
const typeFilter = ref<'all' | DashboardCalendarEvent['type']>('all')

const todayKey = computed(() => toDateKey(new Date()))

const monthItems = computed(() =>
  Array.from({ length: 12 }, (_, month) => ({
    label: formatDatePart(new Date(2020, month, 1), { month: 'long' }),
    value: month,
  })),
)

const yearItems = computed(() => {
  const current = new Date().getFullYear()
  const years = new Set<number>()
  for (let y = current - 10; y <= current + 10; y++) years.add(y)
  years.add(viewCursor.value.getFullYear())
  for (const event of props.events) {
    const y = parseEventDate(event.start).getFullYear()
    if (Number.isFinite(y)) years.add(y)
  }
  return [...years]
    .sort((a, b) => b - a)
    .map(year => ({ label: String(year), value: year }))
})

const selectedMonth = computed({
  get: () => viewCursor.value.getMonth(),
  set: (month: number | string) => {
    viewCursor.value = new Date(viewCursor.value.getFullYear(), Number(month), 1)
  },
})

const selectedYear = computed({
  get: () => viewCursor.value.getFullYear(),
  set: (year: number | string) => {
    viewCursor.value = new Date(Number(year), viewCursor.value.getMonth(), 1)
  },
})

const monthYearLabel = computed(() =>
  formatDatePart(viewCursor.value, { month: 'long', year: 'numeric' }),
)

const weekdayLabels = computed(() => {
  const first = startOfWeek(new Date(), localization.value.firstDayOfWeek)
  return Array.from({ length: 7 }, (_, i) => {
    const d = addDays(first, i)
    return formatDatePart(d, { weekday: 'short' })
  })
})

const weeks = computed(() => buildMonthWeeks(viewCursor.value, localization.value.firstDayOfWeek))

const filteredEvents = computed(() => {
  if (typeFilter.value === 'all') return props.events
  return props.events.filter(event => event.type === typeFilter.value)
})

const eventsByDay = computed(() => {
  const map = new Map<string, DashboardCalendarEvent[]>()
  for (const event of filteredEvents.value) {
    const key = toDateKey(parseEventDate(event.start))
    const list = map.get(key) || []
    list.push(event)
    map.set(key, list)
  }
  for (const [, list] of map) {
    list.sort((a, b) => String(a.start).localeCompare(String(b.start)))
  }
  return map
})

const selectedEvents = computed(() => eventsByDay.value.get(selectedKey.value) || [])

const selectedLabel = computed(() => {
  const d = parseDateKey(selectedKey.value)
  return formatDatePart(d, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
})

const selectUi = {
  base: 'rounded-lg bg-elevated ring-0 font-medium text-highlighted',
  trailingIcon: 'text-muted',
}

const navBtnClass = 'rounded-lg bg-elevated'

const moreItems = computed(() => [
  [
    {
      label: t('docetra.dashboard.calendar.filterAll'),
      icon: typeFilter.value === 'all' ? 'i-lucide-check' : 'i-lucide-list-filter',
      onSelect: () => { typeFilter.value = 'all' },
    },
    {
      label: t('docetra.dashboard.eventType.meeting'),
      icon: typeFilter.value === 'meeting' ? 'i-lucide-check' : 'i-lucide-video',
      onSelect: () => { typeFilter.value = 'meeting' },
    },
    {
      label: t('docetra.dashboard.eventType.deadline'),
      icon: typeFilter.value === 'deadline' ? 'i-lucide-check' : 'i-lucide-alarm-clock',
      onSelect: () => { typeFilter.value = 'deadline' },
    },
    {
      label: t('docetra.dashboard.eventType.record'),
      icon: typeFilter.value === 'record' ? 'i-lucide-check' : 'i-lucide-file-text',
      onSelect: () => { typeFilter.value = 'record' },
    },
    {
      label: t('docetra.dashboard.eventType.upload'),
      icon: typeFilter.value === 'upload' ? 'i-lucide-check' : 'i-lucide-upload',
      onSelect: () => { typeFilter.value = 'upload' },
    },
  ],
  [
    {
      label: t('docetra.dashboard.calendar.viewAll'),
      icon: 'i-lucide-external-link',
      onSelect: () => navigateTo('/meetings/history'),
    },
  ],
])

function prevMonth() {
  viewCursor.value = addMonths(viewCursor.value, -1)
}

function nextMonth() {
  viewCursor.value = addMonths(viewCursor.value, 1)
}

function selectDay(date: Date) {
  selectedKey.value = toDateKey(date)
  emit('daySelect', selectedKey.value)
}

function onEventClick(event: DashboardCalendarEvent, e: Event) {
  e.stopPropagation()
  emit('eventClick', event)
  const path = safeInternalPath(event.href)
  if (path) navigateTo(path)
}

function dayEvents(date: Date) {
  return eventsByDay.value.get(toDateKey(date)) || []
}

function colorClass(color?: DashboardCalendarEvent['color']) {
  switch (color) {
    case 'success': return 'bg-success/15 text-success ring-success/20'
    case 'warning': return 'bg-warning/15 text-warning ring-warning/20'
    case 'error': return 'bg-error/15 text-error ring-error/20'
    case 'info': return 'bg-info/15 text-info ring-info/20'
    case 'neutral': return 'bg-elevated text-muted ring-default'
    default: return 'bg-primary/15 text-primary ring-primary/20'
  }
}

function dotClass(color?: DashboardCalendarEvent['color']) {
  switch (color) {
    case 'success': return 'bg-success'
    case 'warning': return 'bg-warning'
    case 'error': return 'bg-error'
    case 'info': return 'bg-info'
    case 'neutral': return 'bg-muted'
    default: return 'bg-primary'
  }
}

function typeLabel(type?: DashboardCalendarEvent['type']) {
  if (!type) return ''
  return t(`docetra.dashboard.eventType.${type}`)
}

function toDateKey(d: Date) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function parseDateKey(key: string) {
  const [y, m, d] = key.split('-').map(Number)
  return new Date(y!, (m || 1) - 1, d || 1)
}

function parseEventDate(value: string) {
  return new Date(`${value.slice(0, 10)}T12:00:00`)
}

function startOfMonth(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

function addDays(d: Date, n: number) {
  const next = new Date(d)
  next.setDate(next.getDate() + n)
  return next
}

function addMonths(d: Date, n: number) {
  return new Date(d.getFullYear(), d.getMonth() + n, 1)
}

function startOfWeek(d: Date, firstDay: number) {
  const day = d.getDay()
  const normalizedFirstDay = Math.min(6, Math.max(0, Number(firstDay) || 0))
  const diff = -((day - normalizedFirstDay + 7) % 7)
  return addDays(new Date(d.getFullYear(), d.getMonth(), d.getDate()), diff)
}

function buildMonthWeeks(monthStart: Date, firstDay: number) {
  const first = startOfWeek(monthStart, firstDay)
  const lastDay = new Date(monthStart.getFullYear(), monthStart.getMonth() + 1, 0)
  const end = addDays(startOfWeek(lastDay, firstDay), 6)
  const weeks: Date[][] = []
  let cursor = first
  while (cursor.getTime() <= end.getTime()) {
    const week: Date[] = []
    for (let d = 0; d < 7; d++) {
      week.push(cursor)
      cursor = addDays(cursor, 1)
    }
    weeks.push(week)
  }
  return weeks
}

function isSameMonth(d: Date) {
  return d.getMonth() === viewCursor.value.getMonth()
    && d.getFullYear() === viewCursor.value.getFullYear()
}
</script>

<template>
  <section class="flex min-h-128 flex-col overflow-hidden rounded-md border border-default bg-default lg:min-h-144">
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-default px-3 py-2.5 sm:px-4">
      <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        <div class="flex items-center gap-1.5">
          <UButton
            icon="i-lucide-chevron-left"
            color="neutral"
            variant="soft"
            size="sm"
            square
            :class="navBtnClass"
            :aria-label="$t('docetra.dashboard.calendar.prevMonth')"
            @click="prevMonth"
          />
          <UButton
            icon="i-lucide-chevron-right"
            color="neutral"
            variant="soft"
            size="sm"
            square
            :class="navBtnClass"
            :aria-label="$t('docetra.dashboard.calendar.nextMonth')"
            @click="nextMonth"
          />
        </div>

        <h2 class="sr-only">
          {{ monthYearLabel }}
        </h2>
      </div>

      <div class="flex shrink-0 flex-wrap items-center justify-end gap-1.5">
        <USelect
          v-model="selectedMonth"
          :items="monthItems"
          value-key="value"
          size="sm"
          class="w-36"
          :aria-label="$t('docetra.dashboard.calendar.pickMonth')"
          :ui="selectUi"
        />

        <USelect
          v-model="selectedYear"
          :items="yearItems"
          value-key="value"
          size="sm"
          class="w-28"
          :aria-label="$t('docetra.dashboard.calendar.pickYear')"
          :ui="selectUi"
        />

        <UDropdownMenu :items="moreItems" :content="{ align: 'end' }">
          <UButton
            icon="i-lucide-ellipsis"
            color="neutral"
            variant="soft"
            size="sm"
            square
            class="rounded-lg"
            :aria-label="$t('docetra.actions.more')"
          />
        </UDropdownMenu>
      </div>
    </header>

    <div class="flex min-h-0 flex-1 flex-col lg:flex-row">
      <div class="flex min-h-0 min-w-0 flex-1 flex-col">
        <div class="grid grid-cols-7 border-b border-default bg-elevated/40">
          <div
            v-for="label in weekdayLabels"
            :key="label"
            class="px-1 py-2 text-center text-[11px] font-medium uppercase tracking-wide text-muted sm:text-xs"
          >
            {{ label }}
          </div>
        </div>

        <div class="grid min-h-0 flex-1 auto-rows-fr grid-cols-7">
          <div
            v-for="day in weeks.flat()"
            :key="toDateKey(day)"
            role="button"
            tabindex="0"
            class="group relative flex min-h-20 flex-col gap-0.5 border-b border-r border-default p-1 text-left transition hover:bg-elevated/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary sm:min-h-24 sm:p-1.5"
            :class="[
              !isSameMonth(day) ? 'bg-muted/20' : 'bg-default',
              selectedKey === toDateKey(day) ? 'bg-primary/5 ring-1 ring-inset ring-primary/30' : '',
            ]"
            @click="selectDay(day)"
            @keydown.enter.prevent="selectDay(day)"
            @keydown.space.prevent="selectDay(day)"
          >
            <div class="mb-0.5 flex items-center justify-between gap-1">
              <span
                class="inline-flex size-6 items-center justify-center rounded-full text-xs font-medium tabular-nums sm:size-7 sm:text-sm"
                :class="[
                  toDateKey(day) === todayKey
                    ? 'bg-primary text-inverted'
                    : isSameMonth(day) ? 'text-highlighted' : 'text-muted',
                ]"
              >
                {{ day.getDate() }}
              </span>
            </div>

            <div class="flex min-h-0 flex-1 flex-col gap-0.5 overflow-hidden">
              <button
                v-for="event in dayEvents(day).slice(0, maxVisible)"
                :key="event.id"
                type="button"
                class="truncate rounded px-1 py-0.5 text-left text-[10px] font-medium leading-tight ring-1 ring-inset transition hover:brightness-95 sm:text-[11px]"
                :class="colorClass(event.color)"
                :title="event.title"
                @click="onEventClick(event, $event)"
              >
                {{ event.title }}
              </button>
              <span
                v-if="dayEvents(day).length > maxVisible"
                class="px-1 text-[10px] font-medium text-muted"
              >
                {{ $t('docetra.dashboard.calendar.more', { n: dayEvents(day).length - maxVisible }) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <aside class="flex max-h-72 w-full shrink-0 flex-col border-t border-default lg:max-h-none lg:w-72 lg:border-t-0 lg:border-l">
        <div class="border-b border-default px-4 py-3">
          <p class="text-sm font-semibold text-highlighted">{{ selectedLabel }}</p>
          <p class="mt-0.5 text-xs text-muted">
            {{ $t('docetra.dashboard.calendar.eventsCount', { n: selectedEvents.length }) }}
          </p>
        </div>

        <div class="flex-1 space-y-2 overflow-y-auto p-3">
          <button
            v-for="event in selectedEvents"
            :key="event.id"
            type="button"
            class="flex w-full gap-3 rounded-lg border border-default p-2.5 text-left transition hover:border-primary/35 hover:bg-elevated/40"
            @click="onEventClick(event, $event)"
          >
            <span class="mt-1 size-2.5 shrink-0 rounded-full" :class="dotClass(event.color)" />
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-highlighted">{{ event.title }}</p>
              <p class="mt-0.5 text-xs text-muted">
                <span v-if="event.type">{{ typeLabel(event.type) }}</span>
                <span v-if="event.type && event.location"> · </span>
                <span v-if="event.location">{{ event.location }}</span>
                <span v-if="!event.type && !event.location">{{ $t('docetra.dashboard.calendar.allDay') }}</span>
              </p>
            </div>
            <UIcon name="i-lucide-chevron-right" class="mt-0.5 size-4 shrink-0 text-muted" />
          </button>

          <div
            v-if="!selectedEvents.length"
            class="flex flex-col items-center justify-center gap-2 px-4 py-10 text-center"
          >
            <UIcon name="i-lucide-calendar-off" class="size-8 text-muted" />
            <p class="text-sm text-muted">{{ $t('docetra.dashboard.calendar.emptyDay') }}</p>
          </div>
        </div>
      </aside>
    </div>
  </section>
</template>
