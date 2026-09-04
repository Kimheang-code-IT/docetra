<script setup lang="ts">
import { getLocalTimeZone, today } from '@internationalized/date'
import type { CalendarDate, Time } from '@internationalized/date'
import type { DatePickerGranularity } from '~/utils/date-picker'
import {
  isDateTimeGranularity,
  parsePickerValue,
  serializePickerValue,
  datePickerPopoverContent,
  dateFilterFieldLocale,
  toCalendarDate,
  parseTimeValue,
  mergeCalendarDateAndTime,
  getFormDateUi,
} from '~/utils/date-picker'

const props = withDefaults(defineProps<{
  modelValue?: string | null
  disabled?: boolean
  required?: boolean
  granularity?: DatePickerGranularity
  color?: 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'
  variant?: 'outline' | 'soft' | 'subtle' | 'ghost' | 'none'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  class?: string
  placeholder?: string
}>(), {
  granularity: 'day',
  color: 'neutral',
  variant: 'soft',
  size: 'md',
})

const emit = defineEmits<{
  'update:modelValue': [string]
}>()

const { t, locale } = useI18n()

const isDateTime = computed(() => isDateTimeGranularity(props.granularity))
const fieldLocale = computed(() => dateFilterFieldLocale(locale.value))
const formUi = computed(() => getFormDateUi(true))

const dateInput = useTemplateRef<{ inputsRef?: Array<{ $el?: HTMLElement }> } | null>('dateInput')
const dateAnchor = useTemplateRef<HTMLElement | null>('dateAnchor')

const parsed = computed(() => parsePickerValue(props.modelValue, isDateTime.value))

const dateValue = computed({
  get: () => {
    if (!isDateTime.value) {
      return parsePickerValue(props.modelValue, false) as CalendarDate | undefined
    }
    return toCalendarDate(parsed.value)
  },
  set: (value: CalendarDate | undefined | null) => {
    if (!value) {
      emit('update:modelValue', '')
      return
    }
    if (!isDateTime.value) {
      emit('update:modelValue', serializePickerValue(value))
      return
    }
    emit('update:modelValue', mergeCalendarDateAndTime(value, timeValue.value))
  },
})

const timeValue = computed({
  get: () => parseTimeValue(props.modelValue),
  set: (value: Time | undefined | null) => {
    const baseDate = toCalendarDate(parsed.value) || today(getLocalTimeZone())
    emit('update:modelValue', mergeCalendarDateAndTime(baseDate, value ?? undefined))
  },
})
</script>

<template>
  <div
    class="app-input-date flex min-w-0 gap-2"
    :class="[props.class, isDateTime ? 'flex-row items-start' : 'w-full']"
  >
    <!-- Date — Nuxt UI segmented input + calendar popover (ERPNext-style outline field) -->
    <div
      ref="dateAnchor"
      class="min-w-0"
      :class="isDateTime ? 'flex-1' : 'w-full'"
    >
      <UInputDate
        ref="dateInput"
        v-model="dateValue"
        fixed
        trailing
        granularity="day"
        hide-time-zone
        :locale="fieldLocale"
        :disabled="disabled"
        :required="required"
        :size="size"
        :color="color"
        :variant="variant"
        class="w-full min-w-0"
        :ui="formUi"
        :aria-label="placeholder || $t('docetra.common.selectDate')"
      >
        <template #trailing>
          <UPopover
            :reference="dateAnchor ?? dateInput?.inputsRef?.[0]?.$el"
            :content="datePickerPopoverContent"
          >
            <UButton
              color="neutral"
              variant="link"
              :size="size === 'xs' || size === 'sm' ? 'sm' : size"
              icon="i-lucide-calendar"
              class="shrink-0 px-2 text-muted"
              :aria-label="$t('docetra.common.selectDate')"
              :disabled="disabled"
            />

            <template #content>
              <UCalendar
                v-model="dateValue"
                class="p-2"
                :number-of-months="1"
                size="sm"
                :locale="fieldLocale"
                :disabled="disabled"
              />
            </template>
          </UPopover>
        </template>
      </UInputDate>
    </div>

    <!-- Time — separate Nuxt UI time field (datetime only) -->
    <UInputTime
      v-if="isDateTime"
      v-model="timeValue"
      fixed
      trailing
      trailing-icon="i-lucide-clock"
      granularity="minute"
      :hour-cycle="24"
      hide-time-zone
      :locale="fieldLocale"
      :disabled="disabled"
      :required="required"
      :size="size"
      :color="color"
      :variant="variant"
      class="w-36 shrink-0"
      :ui="formUi"
      :aria-label="$t('docetra.common.selectTime')"
    />
  </div>
</template>
