<script setup lang="ts">
import type { DateValue } from '@internationalized/date'
import type { DatePickerGranularity } from '~/utils/date-picker'
import {
  isDateTimeGranularity,
  parsePickerValue,
  serializePickerValue,
  datePickerPopoverContent,
} from '~/utils/date-picker'
import { getFilterDateUi, isFilterValueActive } from '~/utils/filter/select-ui'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

const props = withDefaults(defineProps<{
  modelValue?: string | null
  disabled?: boolean
  required?: boolean
  granularity?: DatePickerGranularity
  color?: 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'
  variant?: 'outline' | 'soft' | 'subtle' | 'ghost' | 'solid' | 'link'
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

const { t } = useI18n()
const { formatDate, formatDateTime } = useAppLocalization()
const open = ref(false)

const isDateTime = computed(() => isDateTimeGranularity(props.granularity))
const isActive = computed(() => isFilterValueActive(props.modelValue))
const dateUi = computed(() => getFilterDateUi(isActive.value, {
  isDateTime: isDateTime.value,
  isRange: false,
  fullWidth: true,
}))

const pickerIcon = computed(() =>
  isDateTime.value ? 'i-lucide-calendar-clock' : 'i-lucide-calendar',
)

const dateValue = computed({
  get: () => parsePickerValue(props.modelValue, isDateTime.value),
  set: (value: DateValue | null | undefined) => {
    emit('update:modelValue', serializePickerValue(value))
  },
})

const displayValue = computed(() => {
  const raw = String(props.modelValue || '').trim()
  if (!raw) return ''
  return isDateTime.value
    ? formatDateTime(raw, '')
    : formatDate(raw, '')
})

const placeholderText = computed(() =>
  props.placeholder
  || (isDateTime.value
    ? t('docetra.common.selectDateTime')
    : t('docetra.common.selectDate')),
)

/** Same width as other form fields; trailing calendar icon like UInput. */
const triggerUi = computed(() => ({
  base: [
    dateUi.value.base,
    'inline-flex w-full items-center justify-between gap-2 px-2.5 text-left font-normal',
    props.size === 'xs' ? 'h-7 text-xs' : '',
    props.size === 'sm' ? 'h-8 text-sm' : '',
    props.size === 'md' ? 'h-9 text-sm' : '',
    props.size === 'lg' ? 'h-10 text-base' : '',
    props.size === 'xl' ? 'h-11 text-base' : '',
  ].filter(Boolean).join(' '),
}))
</script>

<template>
  <div
    class="app-input-date relative min-w-0 w-full"
    :class="props.class"
  >
    <UPopover
      v-model:open="open"
      :content="datePickerPopoverContent"
      :disabled="disabled"
    >
      <UButton
        type="button"
        :color="color"
        :variant="variant"
        :size="size"
        :disabled="disabled"
        :aria-required="required || undefined"
        :aria-label="placeholderText"
        :aria-expanded="open"
        block
        :ui="triggerUi"
      >
        <span
          class="min-w-0 flex-1 truncate tabular-nums"
          :class="displayValue ? 'text-highlighted' : 'text-muted'"
        >
          {{ displayValue || placeholderText }}
        </span>
        <UIcon :name="pickerIcon" class="size-4 shrink-0 text-muted" />
      </UButton>

      <template #content>
        <CommonAppDatePickerPopover
          v-model="dateValue"
          mode="single"
          :granularity="granularity"
          :number-of-months="1"
          :disabled="disabled"
        />
      </template>
    </UPopover>
  </div>
</template>
