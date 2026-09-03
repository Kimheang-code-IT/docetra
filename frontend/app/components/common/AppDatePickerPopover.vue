<script setup lang="ts">
import { CalendarDate, CalendarDateTime, getLocalTimeZone, today } from '@internationalized/date'
import type { DateValue } from '@internationalized/date'
import type { DatePickerGranularity } from '~/utils/date-picker'
import {
  isDateTimeGranularity,
  mergeDateWithTime,
  toCalendarDate,
} from '~/utils/date-picker'

const props = withDefaults(defineProps<{
  mode?: 'single' | 'range'
  granularity?: DatePickerGranularity
  locale?: string
  disabled?: boolean
  /** Page filters use 2 months; document fields keep 1. */
  numberOfMonths?: 1 | 2
}>(), {
  mode: 'single',
  granularity: 'day',
  numberOfMonths: 1,
})

/** Single date / datetime — shared with field v-model. */
const modelValue = defineModel<DateValue | undefined>()
/** Range — shared with filter range v-model. */
const rangeValue = defineModel<{ start: DateValue, end: DateValue } | undefined>('rangeValue')

const { t } = useI18n()

const isDateTime = computed(() => isDateTimeGranularity(props.granularity))
const calendarSize = computed(() => 'xs' as const)

const hourItems = computed(() =>
  Array.from({ length: 24 }, (_, hour) => ({
    label: String(hour).padStart(2, '0'),
    value: String(hour),
  })),
)

const minuteItems = computed(() =>
  Array.from({ length: 60 }, (_, minute) => ({
    label: String(minute).padStart(2, '0'),
    value: String(minute),
  })),
)

const initialPlaceholder = today(getLocalTimeZone())
const placeholder = ref(new CalendarDate(
  initialPlaceholder.year,
  initialPlaceholder.month,
  initialPlaceholder.day,
))
const placeholderBinding = computed({
  get: () => placeholder.value as unknown as DateValue,
  set: (value: DateValue | undefined) => {
    if (!value) return
    placeholder.value = new CalendarDate(value.year, value.month, value.day)
  },
})

const singleCalendar = computed({
  get: () => toCalendarDate(modelValue.value),
  set: (value: CalendarDate | undefined | null) => {
    if (!value) {
      modelValue.value = undefined
      return
    }
    if (isDateTime.value) {
      modelValue.value = mergeDateWithTime(value, modelValue.value)
      return
    }
    modelValue.value = value
  },
})

const rangeCalendar = computed({
  get() {
    if (props.mode !== 'range') return undefined
    const value = rangeValue.value
    if (!value?.start && !value?.end) return undefined

    return {
      start: toCalendarDate(value.start) ?? toCalendarDate(value.end)!,
      end: toCalendarDate(value.end) ?? toCalendarDate(value.start)!,
    }
  },
  set(value: { start: CalendarDate, end: CalendarDate } | null | undefined) {
    if (props.mode !== 'range') return
    if (!value?.start && !value?.end) {
      rangeValue.value = undefined
      return
    }

    const current = rangeValue.value
    if (isDateTime.value) {
      rangeValue.value = {
        start: mergeDateWithTime(value.start, current?.start, 0, 0),
        end: mergeDateWithTime(value.end ?? value.start, current?.end, 23, 59),
      }
      return
    }

    rangeValue.value = {
      start: value.start,
      end: value.end ?? value.start,
    }
  },
})

function readTimePart(value: DateValue | undefined, bound: 'start' | 'end') {
  if (value && 'hour' in value) {
    return { hour: value.hour, minute: value.minute }
  }
  return bound === 'end'
    ? { hour: 23, minute: 59 }
    : { hour: 0, minute: 0 }
}

function writeSingleTime(hour: number, minute: number) {
  const base = toCalendarDate(modelValue.value) || today(getLocalTimeZone())
  modelValue.value = new CalendarDateTime(base.year, base.month, base.day, hour, minute)
}

function writeRangeTime(bound: 'start' | 'end', hour: number, minute: number) {
  const current = rangeValue.value
  const source = bound === 'start' ? current?.start : current?.end
  const base = toCalendarDate(source) || today(getLocalTimeZone())
  const next = new CalendarDateTime(base.year, base.month, base.day, hour, minute)
  rangeValue.value = {
    start: bound === 'start' ? next : (current?.start ?? next),
    end: bound === 'end' ? next : (current?.end ?? next),
  }
}

function timeSelectModel(
  getParts: () => { hour: number, minute: number },
  write: (hour: number, minute: number) => void,
  part: 'hour' | 'minute',
) {
  return computed({
    get: () => String(getParts()[part]),
    set: (value: string | number | null | undefined) => {
      const parts = getParts()
      const next = Number(value)
      if (!Number.isFinite(next)) return
      if (part === 'hour') write(next, parts.minute)
      else write(parts.hour, next)
    },
  })
}

const singleHour = timeSelectModel(
  () => readTimePart(modelValue.value, 'start'),
  writeSingleTime,
  'hour',
)
const singleMinute = timeSelectModel(
  () => readTimePart(modelValue.value, 'start'),
  writeSingleTime,
  'minute',
)
const rangeStartHour = timeSelectModel(
  () => readTimePart(rangeValue.value?.start, 'start'),
  (h, m) => writeRangeTime('start', h, m),
  'hour',
)
const rangeStartMinute = timeSelectModel(
  () => readTimePart(rangeValue.value?.start, 'start'),
  (h, m) => writeRangeTime('start', h, m),
  'minute',
)
const rangeEndHour = timeSelectModel(
  () => readTimePart(rangeValue.value?.end, 'end'),
  (h, m) => writeRangeTime('end', h, m),
  'hour',
)
const rangeEndMinute = timeSelectModel(
  () => readTimePart(rangeValue.value?.end, 'end'),
  (h, m) => writeRangeTime('end', h, m),
  'minute',
)

function goToday() {
  const now = today(getLocalTimeZone())
  placeholder.value = new CalendarDate(now.year, now.month, now.day)

  if (props.mode === 'single') {
    if (isDateTime.value) {
      const date = new Date()
      modelValue.value = new CalendarDateTime(
        now.year,
        now.month,
        now.day,
        date.getHours(),
        date.getMinutes(),
      )
      return
    }
    modelValue.value = now
    return
  }

  if (isDateTime.value) {
    const date = new Date()
    rangeValue.value = {
      start: new CalendarDateTime(now.year, now.month, now.day, 0, 0),
      end: new CalendarDateTime(now.year, now.month, now.day, date.getHours(), date.getMinutes()),
    }
    return
  }

  rangeValue.value = { start: now, end: now }
}

/** Day-only range: bind UCalendar directly to rangeValue (Nuxt UI pattern). */
const dayRangeCalendar = computed({
  get: () => rangeValue.value as { start: CalendarDate, end: CalendarDate } | undefined,
  set: (value: { start: CalendarDate, end: CalendarDate } | undefined) => {
    rangeValue.value = value
  },
})
</script>

<template>
  <div class="w-fit max-w-full">
    <UCalendar
      v-if="mode === 'single'"
      v-model="singleCalendar"
      v-model:placeholder="placeholderBinding"
      class="p-2"
      :number-of-months="numberOfMonths"
      :size="calendarSize"
      :locale="locale"
      :disabled="disabled"
    />
    <UCalendar
      v-else-if="!isDateTime"
      v-model="dayRangeCalendar"
      v-model:placeholder="placeholderBinding"
      class="p-2"
      range
      :number-of-months="numberOfMonths"
      :size="calendarSize"
      :locale="locale"
      :disabled="disabled"
    />
    <UCalendar
      v-else
      v-model="rangeCalendar"
      v-model:placeholder="placeholderBinding"
      class="p-2"
      range
      :number-of-months="numberOfMonths"
      :size="calendarSize"
      :locale="locale"
      :disabled="disabled"
    />

    <div
      class="flex flex-wrap items-end gap-2 border-t border-default px-2 pb-2 pt-2"
      :class="isDateTime ? 'justify-between' : 'justify-end'"
    >
      <div
        v-if="isDateTime && mode === 'single'"
        class="flex min-w-0 flex-1 items-end gap-2"
      >
        <div class="min-w-0 flex-1 space-y-1">
          <label class="block text-xs font-medium text-muted">
            {{ t('docetra.common.hour') }}
          </label>
          <USelect
            v-model="singleHour"
            :items="hourItems"
            color="neutral"
            variant="outline"
            size="sm"
            :disabled="disabled"
            class="w-full"
          />
        </div>
        <div class="min-w-0 flex-1 space-y-1">
          <label class="block text-xs font-medium text-muted">
            {{ t('docetra.common.minute') }}
          </label>
          <USelect
            v-model="singleMinute"
            :items="minuteItems"
            color="neutral"
            variant="outline"
            size="sm"
            :disabled="disabled"
            class="w-full"
          />
        </div>
      </div>
      <div
        v-else-if="isDateTime && mode === 'range'"
        class="flex min-w-0 flex-1 flex-wrap items-end gap-3"
      >
        <div class="min-w-40 flex-1 space-y-1">
          <label class="block text-xs font-medium text-muted">
            {{ t('docetra.common.startTime') }}
          </label>
          <div class="flex gap-2">
            <USelect
              v-model="rangeStartHour"
              :items="hourItems"
              color="neutral"
              variant="outline"
              size="sm"
              :disabled="disabled"
              class="min-w-0 flex-1"
            />
            <USelect
              v-model="rangeStartMinute"
              :items="minuteItems"
              color="neutral"
              variant="outline"
              size="sm"
              :disabled="disabled"
              class="min-w-0 flex-1"
            />
          </div>
        </div>
        <div class="min-w-40 flex-1 space-y-1">
          <label class="block text-xs font-medium text-muted">
            {{ t('docetra.common.endTime') }}
          </label>
          <div class="flex gap-2">
            <USelect
              v-model="rangeEndHour"
              :items="hourItems"
              color="neutral"
              variant="outline"
              size="sm"
              :disabled="disabled"
              class="min-w-0 flex-1"
            />
            <USelect
              v-model="rangeEndMinute"
              :items="minuteItems"
              color="neutral"
              variant="outline"
              size="sm"
              :disabled="disabled"
              class="min-w-0 flex-1"
            />
          </div>
        </div>
      </div>

      <UButton
        color="neutral"
        variant="outline"
        class="shrink-0 justify-center"
        size="sm"
        :disabled="disabled"
        @click="goToday"
      >
        {{ t('docetra.common.today') }}
      </UButton>
    </div>
  </div>
</template>
