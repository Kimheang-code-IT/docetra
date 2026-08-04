<script setup lang="ts">
import { CalendarDate, CalendarDateTime, parseDate, parseDateTime } from '@internationalized/date'
import type { DateValue } from '@internationalized/date'

const props = withDefaults(defineProps<{
  modelValue?: string | null
  disabled?: boolean
  required?: boolean
  granularity?: 'day' | 'hour' | 'minute' | 'second'
  color?: 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'
  variant?: 'outline' | 'soft' | 'subtle' | 'ghost' | 'none'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  class?: string
}>(), {
  granularity: 'day',
  color: 'neutral',
  variant: 'soft',
  size: 'md',
})

const emit = defineEmits<{
  'update:modelValue': [string]
}>()

const inputDate = useTemplateRef<{ inputsRef?: Array<{ $el?: HTMLElement }> } | null>('inputDate')

const isDateTime = computed(() => props.granularity !== 'day')

const hourItems = Array.from({ length: 24 }, (_, i) => ({
  label: String(i).padStart(2, '0'),
  value: i,
}))

const minuteItems = Array.from({ length: 60 }, (_, i) => ({
  label: String(i).padStart(2, '0'),
  value: i,
}))

function parseValue(value?: string | null): DateValue | undefined {
  if (!value) return undefined
  try {
    if (isDateTime.value) {
      const normalized = value.includes('T')
        ? value.slice(0, 16)
        : `${value.slice(0, 10)}T00:00`
      return parseDateTime(normalized)
    }
    return parseDate(value.slice(0, 10))
  }
  catch {
    return undefined
  }
}

function serializeValue(value?: DateValue | null): string {
  if (!value) return ''
  if ('hour' in value) {
    const dt = value as CalendarDateTime
    const hh = String(dt.hour).padStart(2, '0')
    const mm = String(dt.minute).padStart(2, '0')
    return `${dt.toString().slice(0, 10)}T${hh}:${mm}`
  }
  return value.toString()
}

const dateValue = computed({
  get: () => parseValue(props.modelValue) as any,
  set: (value: DateValue | null | undefined) => {
    emit('update:modelValue', serializeValue(value))
  },
})

const calendarRef = computed({
  get: () => {
    const value = dateValue.value
    if (!value) return undefined
    if ('hour' in value) {
      return new CalendarDate(value.year, value.month, value.day)
    }
    return value
  },
  set: (value: CalendarDate | undefined | null) => {
    if (!value) {
      dateValue.value = null
      return
    }
    if (isDateTime.value) {
      const current = dateValue.value as CalendarDateTime | undefined
      dateValue.value = new CalendarDateTime(
        value.year,
        value.month,
        value.day,
        current?.hour ?? 0,
        current?.minute ?? 0,
      )
      return
    }
    dateValue.value = value
  },
})

const selectedHour = computed({
  get: () => {
    const value = dateValue.value as CalendarDateTime | undefined
    return value && 'hour' in value ? value.hour : 0
  },
  set: (hour: number) => {
    const current = dateValue.value as CalendarDateTime | CalendarDate | undefined
    const base = current || new CalendarDateTime(
      new Date().getFullYear(),
      new Date().getMonth() + 1,
      new Date().getDate(),
      0,
      0,
    )
    dateValue.value = new CalendarDateTime(
      base.year,
      base.month,
      base.day,
      hour,
      'minute' in base ? base.minute : 0,
    )
  },
})

const selectedMinute = computed({
  get: () => {
    const value = dateValue.value as CalendarDateTime | undefined
    return value && 'minute' in value ? value.minute : 0
  },
  set: (minute: number) => {
    const current = dateValue.value as CalendarDateTime | CalendarDate | undefined
    const base = current || new CalendarDateTime(
      new Date().getFullYear(),
      new Date().getMonth() + 1,
      new Date().getDate(),
      0,
      0,
    )
    dateValue.value = new CalendarDateTime(
      base.year,
      base.month,
      base.day,
      'hour' in base ? base.hour : 0,
      minute,
    )
  },
})

const trailingReference = computed(() => {
  const inputs = inputDate.value?.inputsRef || []
  const el = inputs[inputs.length - 1]?.$el || inputs[0]?.$el
  return el
})
</script>

<template>
  <UInputDate
    ref="inputDate"
    v-model="dateValue"
    :granularity="granularity"
    :disabled="disabled"
    :required="required"
    :color="color"
    :variant="variant"
    :size="size"
    :class="props.class || 'w-full'"
  >
    <template #trailing>
      <UPopover :reference="trailingReference">
        <UButton
          color="neutral"
          variant="link"
          size="sm"
          :icon="isDateTime ? 'i-lucide-calendar-clock' : 'i-lucide-calendar'"
          :aria-label="isDateTime ? 'Select date and time' : 'Select a date'"
          class="px-0"
          :disabled="disabled"
        />
        <template #content>
          <div class="space-y-2 p-2">
            <UCalendar v-model="calendarRef" />
            <div
              v-if="isDateTime"
              class="flex items-center gap-2 border-t border-default pt-2"
            >
              <USelect
                v-model="selectedHour"
                :items="hourItems"
                value-key="value"
                label-key="label"
                size="sm"
                class="w-20"
                :disabled="disabled"
                aria-label="Hour"
              />
              <span class="text-sm text-muted" aria-hidden="true">:</span>
              <USelect
                v-model="selectedMinute"
                :items="minuteItems"
                value-key="value"
                label-key="label"
                size="sm"
                class="w-20"
                :disabled="disabled"
                aria-label="Minute"
              />
            </div>
          </div>
        </template>
      </UPopover>
    </template>
  </UInputDate>
</template>
